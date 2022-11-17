import logging
from functools import wraps

from flask import g, redirect, session, url_for, abort, render_template
from flask_dance.contrib.github import github as gh_auth
from cachetools import cached
from cachetools.keys import hashkey
from github import Github, Repository
from github import UnknownObjectException, RateLimitExceededException, GithubException

from utils import cache
from errors import SAML403
from config import GITHUB_ACCESS_TOKEN
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
            raise SAML403(config_repo)
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
            raise SAML403(config_repo)
        log.error(e, e.__traceback__)
        abort(500, description="Error while listing commits")


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
