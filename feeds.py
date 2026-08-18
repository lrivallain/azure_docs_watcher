"""RSS feed generation.

A subscribed reader polls the same feed URL every few minutes, forever, and the
answer only changes when a new commit lands. Two things follow, and both live
here:

* the serialized body is cached, so repeated polls do not rebuild it;
* the body is a pure function of its arguments, which makes its hash a usable
  ``ETag``. The view turns that into a ``304 Not Modified``, which is where the
  bandwidth is actually saved.

This module therefore has no Flask dependency: every request dependent value is
passed in, which is what keeps the cache key honest.
"""

import datetime
import hashlib
import logging
import threading
from typing import NamedTuple

from cachetools import TTLCache
from feedgen.feed import FeedGenerator

from config import (
    APP_AUTHOR,
    APP_AUTHOR_EMAIL,
    APP_DESCRIPTION,
    CACHE_SIZE,
    CACHE_TTL,
)

log = logging.getLogger(__name__)

_render_cache = TTLCache(maxsize=CACHE_SIZE, ttl=CACHE_TTL)
_render_lock = threading.Lock()


class FeedPayload(NamedTuple):
    """A serialized feed and the HTTP validators describing it.

    Attributes:
        body (bytes): the serialized RSS document.
        etag (str): a strong validator, the hash of ``body``.
        last_modified (datetime.datetime): date of the newest commit.
    """

    body: bytes
    etag: str
    last_modified: datetime.datetime


def _entry_title(message: str) -> str:
    """Build a readable feed entry title out of a commit message.

    Args:
        message (str): the full commit message.

    Returns:
        str: the first meaningful line of the message.
    """
    for line in (message or "").splitlines():
        line = line.strip()
        if line:
            return line
    return "(no commit message)"


def _last_modified(commits: list) -> datetime.datetime:
    """Date the feed as a whole, from its newest commit.

    Args:
        commits (list): the commits to publish.

    Returns:
        datetime.datetime: the newest commit date, or now for an empty feed.
    """
    dates = [commit["date"] for commit in commits if commit.get("date")]
    moment = max(dates) if dates else datetime.datetime.now(datetime.timezone.utc)
    # HTTP dates carry no sub-second part. Truncating here keeps the value sent
    # in Last-Modified identical to the one a reader echoes back in
    # If-Modified-Since, which would otherwise never compare as equal.
    return moment.replace(microsecond=0)


def _fingerprint(commits: list) -> str:
    """Summarize a commit list into a cache key component.

    A commit is immutable, so its sha stands for its whole content: hashing the
    shas, in order, is enough to detect any change to the feed body.

    Args:
        commits (list): the commits to publish.

    Returns:
        str: a hexadecimal digest.
    """
    digest = hashlib.sha256()
    for commit in commits:
        digest.update(f"{commit.get('sha', '')}\n".encode())
    return digest.hexdigest()


def _build_feed(
    commits: list,
    folder: str,
    repo: dict,
    page_url: str,
    feed_url: str,
    logo_url: str,
    updated: datetime.datetime,
) -> bytes:
    """Serialize a list of commits as an RSS document.

    Args:
        commits (list): commits to publish, most recent first.
        folder (str): watched path, used in the feed title.
        repo (dict): repository configuration.
        page_url (str): absolute URL of the matching HTML page.
        feed_url (str): absolute URL of the feed itself.
        logo_url (str): absolute URL of the repository icon, may be None.
        updated (datetime.datetime): date of the feed as a whole.

    Returns:
        bytes: the serialized RSS feed.
    """
    log.debug("Generating RSS feed for %s %s", repo.get("name"), folder)
    feed = FeedGenerator()
    # Dublin Core carries the commit author without exposing an email address.
    feed.load_extension("dc")

    feed.id(feed_url)
    feed.title(f"{repo.get('display_name')} changes in section '{folder}'")
    feed.author({"name": APP_AUTHOR, "email": APP_AUTHOR_EMAIL})
    # feedgen lets the last registered link win for the RSS <link> element, so
    # the alternate one must be declared after the self one.
    feed.link(href=feed_url, rel="self")
    feed.link(href=page_url, rel="alternate")
    feed.subtitle(APP_DESCRIPTION.replace("__repo__", repo.get("display_name")))
    feed.language("en")
    if logo_url:
        feed.logo(logo_url)

    for commit in commits:
        # feedgen prepends entries by default, which would publish the feed in
        # ascending date order.
        entry = feed.add_entry(order="append")
        # The commit URL is a stable, unique and resolvable identifier.
        entry.id(commit.get("url"))
        entry.guid(commit.get("url"), permalink=True)
        entry.link(href=commit.get("url"))
        entry.title(_entry_title(commit.get("message")))
        # Publishing the whole message lets readers show the full context.
        entry.description(commit.get("message"))
        if commit.get("author"):
            entry.dc.dc_creator(commit.get("author"))
        if commit.get("date"):
            entry.published(commit["date"])
            entry.updated(commit["date"])

    feed.updated(updated)
    return feed.rss_str(pretty=True)


def get_feed(
    commits: list,
    folder: str,
    repo: dict,
    page_url: str,
    feed_url: str,
    logo_url: str = None,
) -> FeedPayload:
    """Build, or replay from the cache, the RSS feed of a list of commits.

    Args:
        commits (list): commits to publish, most recent first.
        folder (str): watched path, used in the feed title.
        repo (dict): repository configuration.
        page_url (str): absolute URL of the matching HTML page.
        feed_url (str): absolute URL of the feed itself.
        logo_url (str, optional): absolute URL of the repository icon.

    Returns:
        FeedPayload: the serialized feed and its HTTP validators.
    """
    # Everything the body is built from takes part in the key, so a cache hit
    # can only ever return the exact document the arguments describe. The host
    # and scheme reach the key through the two absolute URLs.
    key = (
        feed_url,
        page_url,
        logo_url,
        folder,
        repo.get("display_name"),
        _fingerprint(commits),
    )
    with _render_lock:
        payload = _render_cache.get(key)
    if payload is not None:
        log.debug("Serving the cached feed of %s %s", repo.get("name"), folder)
        return payload

    updated = _last_modified(commits)
    body = _build_feed(commits, folder, repo, page_url, feed_url, logo_url, updated)
    payload = FeedPayload(
        body=body,
        etag=hashlib.sha256(body).hexdigest(),
        last_modified=updated,
    )
    with _render_lock:
        _render_cache[key] = payload
    return payload
