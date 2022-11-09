import logging
from functools import wraps

from flask import g, redirect, session, url_for
from flask_dance.contrib.github import github as gh_auth
from cachetools import cached
from cachetools.keys import hashkey
from github import Github, Repository

from utils import cache
from config import GITHUB_ACCESS_TOKEN

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
    return repo.get_dir_contents(path)


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
    return g.gh.get_repo(f"{config_repo['owner']}/{config_repo['repository']}")


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
