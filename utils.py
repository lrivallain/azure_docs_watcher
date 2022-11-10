"""
"""
import datetime
import logging
from markupsafe import escape

from github import Repository
from github import UnknownObjectException, RateLimitExceededException
from flask import request, url_for, abort
from feedgen.feed import FeedGenerator
from cachetools import cached, TTLCache

from config import *

# Configure cache
cache = TTLCache(maxsize=CACHE_SIZE, ttl=CACHE_TTL)
cache_home = TTLCache(
    maxsize=CACHE_SIZE, ttl=CACHE_TTL * 10
)  # 10 times longer than the other cache for the home page

log = logging.getLogger(__name__)


def get_repo_config(repo_owner: str = None, repo_name: str = None) -> dict:
    """Get the configuration for a given repo.
    If not configured, returns a faked configuration.

    Args:
        repo_owner (str, optional): GitHub repo owner. Defaults to None.
        repo_name (str, optional): GitHub repo name. Defaults to None.
        path (str, optional): Path to the file or folder. Defaults to "".

    Returns:
        dict: Repo configuration
    """
    log.debug(f"Getting repo configuration")
    if not repo_owner and repo_name:
        abort(400, "Missing repository owner or name")
    repo_keyname = "/".join([repo_owner, repo_name])
    log.debug(f"Looking for repository {repo_keyname} in configuration")
    config_repo = AZURE_DOCS_REPOS.get(repo_keyname)
    if not config_repo:
        log.debug(
            "Repository not found in configuration: format custom repository like a configured one"
        )
        config_repo = {
            "name": repo_keyname,
            "display_name": repo_keyname,
            "owner": repo_owner,
            "repository": repo_name,
            "articles_folder": "/",
            "icon": "",
        }
    return config_repo


@cached(cache)
def get_commits(
    repo: Repository,
    section_path: str,
    since: int = SINCE,
    shared_token: bool = True,
    cache_key: str = None,
) -> list:
    """Get the list of commits for the given repo and folder path.

    Args:
        repo (Repository): GitHub repository
        section_path (str): path to the folder to monitor
        since (int, optional): Number of days to look back. Defaults to SINCE
        shared_token (bool, optional): Use the shared token or the user token. Defaults to True.
        cache_key (str): token based key to use for the cache

    Returns:
        list: list of commits
    """
    log.debug(f"Looking for commits in {section_path}")
    # get commit for the root of the repo requires no prefix slash
    if section_path == "/":
        section_path = ""
    log.debug("Calculating the reference date")
    ref_date = datetime.datetime.now() - datetime.timedelta(days=since)
    try:
        _commits = repo.get_commits(path=section_path, since=ref_date)
    except RateLimitExceededException:
        return abort(429, "Rate limit exceeded")
    except Exception as e:
        log.error(e, e.__traceback__)
        return abort(500, "Error while listing commits")

    log.debug(f"{_commits.totalCount} commits found in the last {since} days")
    # Converting a limited list of commits
    ret_commits = []
    if _commits.totalCount > 0:
        if _commits.totalCount > MAX_COMMITS and shared_token:
            log.info("Using shared Github client: limiting commits to %s", MAX_COMMITS)
            _commits = _commits[:MAX_COMMITS]
        try:
            for commit in _commits:
                ret_commits.append(
                    {
                        "sha": escape(commit.sha[:7]),
                        "author": escape(commit.commit.author.name),
                        "commit": escape(commit.commit),
                        "url": escape(commit.html_url),
                        "message": escape(commit.commit.message),
                        "date": commit.commit.author.date,
                    }
                )
        except Exception as e:
            log.error(e, e.__traceback__)
            return abort(500, "Error while formatting commits")
    return ret_commits


def get_feed(commits: list, folder: str, repo: dict) -> str:
    """Get the RSS feed for the given commits

    Args:
        commits (list): list of commits
        folder (str): folder to track
        repo (dict): GitHub repo from configuration

    Returns:
        str: RSS feed
    """
    log.debug("Generating RSS feed")
    fg = FeedGenerator()
    fg.id(request.base_url)
    fg.title(f"{repo.get('display_name')} changes in section '{folder}'")
    fg.author({"name": APP_AUTHOR, "email": APP_AUTHOR_EMAIL})
    fg.link(
        href=request.base_url,
        rel="alternate",
    )
    fg.logo(url_for("static", filename=repo.get("icon"), _external=True))
    fg.subtitle(APP_DESCRIPTION.replace("__repo__", repo.get("display_name")))
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
