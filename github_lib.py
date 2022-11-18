import datetime
import logging
from functools import wraps
from markupsafe import escape

from flask import g, redirect, session, url_for, abort, render_template
from flask_dance.contrib.github import github as gh_auth
from cachetools import cached
from cachetools.keys import hashkey
from github import Github, Repository
from github import UnknownObjectException, RateLimitExceededException, GithubException

from utils import cache
from errors import SAML403Exception
from config import GITHUB_ACCESS_TOKEN, SINCE, MAX_COMMITS
from base_routes import app

# configure logging
log = logging.getLogger(__name__)


@cached(cache)
def get_repo_contents(repo: Repository, path: str, cache_key: str) -> list:
    """Get the content of a file in a GitHub repo.

    Args:
        repo (Repository): GitHub repo
        path (str): path to the file
        cache_key (str): key to use for the cache

    Returns:
        list: list of contents
    """
    log.debug(f"Listing files and folders in {path}")
    try:
        return repo.get_dir_contents(path)
    except RateLimitExceededException:
        abort(429, "Rate limit exceeded")
    except Exception as e:
        if isinstance(e, GithubException) and "SAML enforcement" in e.data.get(
            "message"
        ):
            raise SAML403Exception(config_repo)
        log.error(e, e.__traceback__)
        abort(500, "Error while listing files and folders")


@cached(cache, key=lambda *args, **kwargs: hashkey(kwargs["cache_key"]))
def get_repo(g, config_repo: dict, cache_key: str) -> Repository:
    """Get the content of a file in a GitHub repo.

    Args:
        g (g): Falsh global object
        config_repo (dict): GitHub repo configuration
        cache_key (str): key to use for the cache

    Returns:
        list: list of contents
    """
    try:
        return g.gh.get_repo(f"{config_repo['owner']}/{config_repo['repository']}")
    except UnknownObjectException:
        abort(404, description="Repository not found on GitHub")
    except Exception as e:
        if isinstance(e, GithubException) and "SAML enforcement" in e.data.get(
            "message"
        ):
            raise SAML403Exception(config_repo)
        log.error(e, e.__traceback__)
        abort(500, description="Error while listing commits")


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
        if isinstance(e, GithubException) and "SAML enforcement" in e.data.get(
            "message"
        ):
            raise SAML403Exception(config_repo)
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


def login_management(f):
    """Decorator to manage the GitHub login suggestion to bypass performance limits.

    Args:
        f (_type_): function to decorate

    Returns:
        function: decorated function
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        log.debug("Checking if user is authenticated")
        g.using_shared_gh = True
        if not gh_auth.authorized:
            g.gh_token = GITHUB_ACCESS_TOKEN
        else:
            resp = gh_auth.get("/user")
            if not resp.json().get("login"):
                log.warn("User used to be authenticated but is not anymore")
                return redirect(url_for("github.login"))
            log.debug("User is authenticated")
            session["username"] = resp.json()["login"]
            g.gh_token = gh_auth.token.get("access_token")
            g.using_shared_gh = False
        g.gh = Github(g.gh_token)
        return f(*args, **kwargs)

    return decorated_function
