"""RSS feed generation."""

import datetime
import logging

from feedgen.feed import FeedGenerator
from flask import request, url_for

from config import APP_AUTHOR, APP_AUTHOR_EMAIL, APP_DESCRIPTION

log = logging.getLogger(__name__)


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


def get_feed(commits: list, folder: str, repo: dict, page_url: str) -> bytes:
    """Build the RSS feed of a list of commits.

    Args:
        commits (list): commits to publish, most recent first.
        folder (str): watched path, used in the feed title.
        repo (dict): repository configuration.
        page_url (str): absolute URL of the matching HTML page.

    Returns:
        bytes: the serialized RSS feed.
    """
    log.debug("Generating RSS feed for %s %s", repo.get("name"), folder)
    feed = FeedGenerator()
    # Dublin Core carries the commit author without exposing an email address.
    feed.load_extension("dc")

    feed.id(request.base_url)
    feed.title(f"{repo.get('display_name')} changes in section '{folder}'")
    feed.author({"name": APP_AUTHOR, "email": APP_AUTHOR_EMAIL})
    # feedgen lets the last registered link win for the RSS <link> element, so
    # the alternate one must be declared after the self one.
    feed.link(href=request.base_url, rel="self")
    feed.link(href=page_url, rel="alternate")
    feed.subtitle(APP_DESCRIPTION.replace("__repo__", repo.get("display_name")))
    feed.language("en")
    if repo.get("icon"):
        feed.logo(url_for("static", filename=repo.get("icon"), _external=True))

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

    dates = [commit["date"] for commit in commits if commit.get("date")]
    feed.updated(max(dates) if dates else datetime.datetime.now(datetime.UTC))

    return feed.rss_str(pretty=True)
