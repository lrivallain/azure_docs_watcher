"""Credential-free access to the public GitHub data the watcher needs.

The application requires two pieces of information, both public:

* the recent commits touching a path, read from the Atom feeds published by the
  GitHub web front-end (``/<owner>/<repo>/commits/<branch>/<path>.atom``). Those
  feeds are not served by ``api.github.com`` and therefore consume no REST API
  rate limit at all;
* the entries of a directory, read anonymously from the REST API.

No credential is involved anywhere. This matters because organizations can cap
personal access token lifetimes to a few days, which used to make the
deployment depend on a recurring manual token renewal.

Known limitation: GitHub serves commit feeds as a single, non paginated page of
at most 20 entries and offers no date filter, so a path cannot expose more
history than that.

This module deliberately has no Flask dependency so it can be tested on its own.
"""

import datetime
import html
import logging
import re
import threading
import xml.etree.ElementTree as ElementTree
from urllib.parse import quote

import requests
from cachetools import TTLCache, cached

from config import (
    CACHE_SIZE,
    CACHE_TTL,
    GITHUB_API_BASE,
    GITHUB_WEB_BASE,
    HTTP_TIMEOUT,
    USER_AGENT,
)
from errors import GitHubError

log = logging.getLogger(__name__)

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}

# ``tag:github.com,2008:Grit::Commit/<sha>``
_COMMIT_ID_RE = re.compile(r"Commit/(?P<sha>[0-9a-f]{7,40})")
# ``Recent Commits to <repository>:<branch>``. Neither a repository name nor a
# git ref may contain a colon, so the last one is an unambiguous separator.
_FEED_TITLE_RE = re.compile(r"^Recent Commits to .*:(?P<branch>.+)$", re.DOTALL)
_PRE_RE = re.compile(r"^\s*<pre[^>]*>(?P<body>.*)</pre>\s*$", re.DOTALL)

# Default branches change very rarely, so they are cached far longer than the
# commit data to avoid spending requests on them.
_branch_cache = TTLCache(maxsize=CACHE_SIZE, ttl=CACHE_TTL * 24)
# Directory listings are the only REST calls left, and anonymous REST is capped
# at 60 requests per hour and per IP: cache them aggressively.
_directory_cache = TTLCache(maxsize=CACHE_SIZE, ttl=CACHE_TTL * 10)
_feed_cache = TTLCache(maxsize=CACHE_SIZE, ttl=CACHE_TTL)

_branch_lock = threading.Lock()
_directory_lock = threading.Lock()
_feed_lock = threading.Lock()


def _request(url: str, accept: str) -> requests.Response:
    """Perform an anonymous GET against GitHub and normalise the failures.

    Args:
        url (str): absolute URL to fetch.
        accept (str): value of the ``Accept`` header.

    Raises:
        GitHubError: on any transport failure or non successful response.

    Returns:
        requests.Response: the successful response.
    """
    headers = {"User-Agent": USER_AGENT, "Accept": accept}
    log.debug("GET %s", url)
    try:
        response = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT)
    except requests.exceptions.Timeout as exc:
        raise GitHubError(504, "GitHub did not answer in time.") from exc
    except OSError as exc:
        # requests.exceptions.RequestException derives from OSError, so this
        # also covers lower level failures such as an unusable CA bundle, which
        # would otherwise surface as an unhandled error.
        log.warning("Transport failure while calling %s: %s", url, exc)
        raise GitHubError(502, "Unable to reach GitHub.") from exc

    if response.status_code == 200:
        return response
    raise GitHubError(response.status_code, _error_message(response))


def _error_message(response: requests.Response) -> str:
    """Turn a failed GitHub response into a message meant for the visitor.

    Args:
        response (requests.Response): the failed response.

    Returns:
        str: a human readable message.
    """
    message = ""
    try:
        payload = response.json()
        if isinstance(payload, dict):
            message = payload.get("message", "")
    except ValueError:  # not a JSON body, e.g. the Atom endpoints
        pass

    if response.status_code == 404:
        return message or "This repository or path does not exist on GitHub."
    if response.status_code in (403, 429):
        return (
            "GitHub is rate limiting this service right now. "
            "Please retry in a few minutes."
        )
    return message or f"Unexpected answer from GitHub ({response.status_code})."


def _parse_date(value: str) -> datetime.datetime:
    """Parse an ISO-8601 timestamp into a timezone aware UTC datetime.

    Args:
        value (str): timestamp such as ``2024-07-30T21:33:41Z``.

    Returns:
        datetime.datetime: the parsed datetime, or None when unparsable.
    """
    if not value:
        return None
    try:
        parsed = datetime.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        log.warning("Unparsable date returned by GitHub: %r", value)
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.UTC)
    return parsed.astimezone(datetime.UTC)


def _parse_feed(content: bytes) -> ElementTree.Element:
    """Parse an Atom document.

    Args:
        content (bytes): the raw feed.

    Raises:
        GitHubError: when the document is not valid XML.

    Returns:
        ElementTree.Element: the feed root element.
    """
    try:
        return ElementTree.fromstring(content)
    except ElementTree.ParseError as exc:
        raise GitHubError(502, "GitHub returned an invalid feed.") from exc


@cached(_branch_cache, lock=_branch_lock)
def get_default_branch(owner: str, repository: str) -> str:
    """Resolve the default branch of a public repository, without credential.

    The branch-less Atom feed always targets the default branch and advertises
    it in its title (``Recent Commits to <repository>:<branch>``). Reading it
    there avoids a REST call, and is required because repositories do not all
    share the same default branch: ``MicrosoftDocs/sql-docs`` uses ``live``.

    Args:
        owner (str): repository owner.
        repository (str): repository name.

    Raises:
        GitHubError: when the repository is unreachable or the title unexpected.

    Returns:
        str: the default branch name.
    """
    url = f"{GITHUB_WEB_BASE}/{quote(owner)}/{quote(repository)}/commits.atom"
    feed = _parse_feed(_request(url, accept="application/atom+xml").content)

    title = feed.findtext("atom:title", default="", namespaces=ATOM_NS)
    match = _FEED_TITLE_RE.match(title.strip())
    if not match:
        raise GitHubError(502, "Unable to detect the default branch of this repository.")

    branch = match.group("branch").strip()
    log.debug("Default branch of %s/%s is %s", owner, repository, branch)
    return branch


def _commit_from_entry(entry: ElementTree.Element) -> dict:
    """Convert an Atom entry into the commit representation used by the views.

    Args:
        entry (ElementTree.Element): an ``<entry>`` element of a commit feed.

    Returns:
        dict: the commit, or None when the entry holds no usable commit.
    """
    match = _COMMIT_ID_RE.search(
        entry.findtext("atom:id", default="", namespaces=ATOM_NS)
    )
    if not match:
        return None

    link = entry.find("atom:link[@rel='alternate']", ATOM_NS)
    if link is None:
        link = entry.find("atom:link", ATOM_NS)

    # The title only holds the first line of the message, whereas the content
    # holds the whole message wrapped in a <pre> block.
    title = (entry.findtext("atom:title", default="", namespaces=ATOM_NS) or "").strip()
    content = entry.findtext("atom:content", default="", namespaces=ATOM_NS) or ""
    body = _PRE_RE.match(content)
    message = html.unescape(body.group("body")).strip() if body else title

    author = entry.find("atom:author", ATOM_NS)
    name = ""
    if author is not None:
        name = (
            author.findtext("atom:name", default="", namespaces=ATOM_NS) or ""
        ).strip()
        if not name:
            # Some commits carry no author name: fall back on the email local
            # part rather than showing an empty author.
            email = (
                author.findtext("atom:email", default="", namespaces=ATOM_NS) or ""
            ).strip()
            name = email.split("@")[0]

    return {
        "sha": match.group("sha"),
        "author": name,
        "url": link.get("href") if link is not None else "",
        "message": message or title,
        "date": _parse_date(
            entry.findtext("atom:updated", default="", namespaces=ATOM_NS)
        ),
    }


@cached(_feed_cache, lock=_feed_lock)
def _get_feed_commits(owner: str, repository: str, path: str) -> tuple:
    """Fetch and parse the whole commit feed of a path.

    The result is cached so that concurrent visitors share a single upstream
    fetch.

    Args:
        owner (str): repository owner.
        repository (str): repository name.
        path (str): path within the repository, may be empty for the root.

    Raises:
        GitHubError: when GitHub cannot be reached or the path does not exist.

    Returns:
        tuple: the parsed commits, most recent first.
    """
    branch = get_default_branch(owner, repository)
    url = f"{GITHUB_WEB_BASE}/{quote(owner)}/{quote(repository)}/commits/{quote(branch)}"
    path = (path or "").strip("/")
    if path:
        url += f"/{quote(path)}"
    url += ".atom"

    feed = _parse_feed(_request(url, accept="application/atom+xml").content)
    commits = []
    for entry in feed.findall("atom:entry", ATOM_NS):
        commit = _commit_from_entry(entry)
        if commit and commit["date"]:
            commits.append(commit)

    log.debug("%s commits found in the feed %s", len(commits), url)
    # A tuple keeps the cached value from being mutated by a caller.
    return tuple(commits)


def get_commits(owner: str, repository: str, path: str) -> list:
    """List the recent commits touching a path of a public repository.

    GitHub caps the feed itself, so no additional limit is applied here.

    Args:
        owner (str): repository owner.
        repository (str): repository name.
        path (str): path within the repository to watch.

    Raises:
        GitHubError: when GitHub cannot be reached or the path does not exist.

    Returns:
        list: the matching commits, most recent first.
    """
    # The feed is normally ordered, but sorting keeps the result correct even if
    # GitHub ever returns the entries out of order.
    commits = [dict(commit) for commit in _get_feed_commits(owner, repository, path)]
    commits.sort(key=lambda commit: commit["date"], reverse=True)
    return commits


@cached(_directory_cache, lock=_directory_lock)
def get_directory(owner: str, repository: str, path: str) -> tuple:
    """List the entries of a directory of a public repository.

    This is the only REST API call left. Anonymous REST is capped at 60
    requests per hour and per IP, hence the long lived cache.

    Args:
        owner (str): repository owner.
        repository (str): repository name.
        path (str): directory to list, may be empty for the repository root.

    Raises:
        GitHubError: when GitHub cannot be reached or the path is not a folder.

    Returns:
        tuple: entries, each holding a ``name``, ``path`` and ``type``.
    """
    path = (path or "").strip("/")
    url = (
        f"{GITHUB_API_BASE}/repos/{quote(owner)}/{quote(repository)}"
        f"/contents/{quote(path)}"
    )
    payload = _request(url, accept="application/vnd.github+json").json()

    if not isinstance(payload, list):
        raise GitHubError(404, "The requested path is not a directory.")

    entries = [
        {
            "name": item.get("name", ""),
            "path": item.get("path", ""),
            "type": item.get("type", ""),
        }
        for item in payload
        # Documentation repositories keep their tooling in dot and underscore
        # prefixed folders (.github, .vscode, .docutune, _bread): those are not
        # documentation sections and only add noise to the listing.
        if item.get("name") and item["name"][0] not in "._"
    ]
    # Folders first, then files, both alphabetically.
    return tuple(sorted(entries, key=lambda e: (e["type"] != "dir", e["name"].lower())))
