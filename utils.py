"""
"""
import datetime
import logging
from markupsafe import escape

from github import Repository
from flask import request, url_for
from feedgen.feed import FeedGenerator

from config import MAX_COMMITS, SINCE, APP_AUTHOR, APP_AUTHOR_EMAIL, APP_DESCRIPTION


log = logging.getLogger(__name__)


def get_commits(
    repo: Repository, section_path: str, since: int = SINCE, shared_token: bool = True
) -> list:
    """Get the list of commits for the given repo and folder path.

    Args:
        repo (Repository): GitHub repository
        section_path (str): path to the folder to monitor
        since (int, optional): Number of days to look back. Defaults to SINCE
        shared_token (bool, optional): Use the shared token or the user token. Defaults to True.

    Returns:
        list: list of commits
    """
    log.debug("Calculating the reference date")
    ref_date = datetime.datetime.now() - datetime.timedelta(days=since)
    _commits = repo.get_commits(path=section_path, since=ref_date)

    log.debug(f"{_commits.totalCount} commits found in the last {since} days")
    # Converting a limited list of commits
    ret_commits = []
    if _commits.totalCount > 0:
        if _commits.totalCount > MAX_COMMITS and shared_token:
            log.info("Using shared Github client: limiting commits to %s", MAX_COMMITS)
            _commits = _commits[:MAX_COMMITS]
        for commit in _commits:
            ret_commits.append(
                {
                    "sha": escape(commit.sha[:7]),
                    "author": escape(commit.author.name),
                    "commit": escape(commit.commit),
                    "url": escape(commit.html_url),
                    "message": escape(commit.commit.message),
                    "date": commit.commit.author.date,
                }
            )
    return ret_commits


def get_feed(commits: list, folder: str) -> str:
    """Get the RSS feed for the given commits

    Args:
        commits (list): list of commits
        folder (str): folder to track

    Returns:
        str: RSS feed
    """
    log.debug("Generating RSS feed")
    fg = FeedGenerator()
    fg.id(request.base_url)
    fg.title(f"Azure Docs changes in section '{folder}'")
    fg.author({"name": APP_AUTHOR, "email": APP_AUTHOR_EMAIL})
    fg.link(
        href=request.base_url,
        rel="alternate",
    )
    fg.logo(url_for("static", filename="favicon.svg", _external=True))
    fg.subtitle(APP_DESCRIPTION)
    fg.link(
        href=request.base_url,
        rel="self",
    )
    fg.language("en")

    for commit in commits[:MAX_COMMITS]:
        fe = fg.add_entry()
        fe.id(commit.get("url"))
        fe.title(commit.get("message"))
        fe.link(href=commit.get("url"))
        fe.author({"name": "", "email": commit.get("author")})
        fe.published(commit.get("date").replace(tzinfo=datetime.timezone.utc))
    return fg.rss_str(pretty=True)
