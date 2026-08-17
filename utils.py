"""Helpers shared by the views."""

import logging

from config import AZURE_DOCS_REPOS, MAX_SINCE, SINCE

log = logging.getLogger(__name__)


def get_repo_config(repo_owner: str, repo_name: str) -> dict:
    """Get the configuration of a repository.

    Repositories that are not part of the curated list are still supported:
    they get a synthetic configuration so that any public repository can be
    watched.

    Args:
        repo_owner (str): GitHub repository owner.
        repo_name (str): GitHub repository name.

    Returns:
        dict: repository configuration.
    """
    repo_keyname = f"{repo_owner}/{repo_name}"
    log.debug("Looking for repository %s in configuration", repo_keyname)
    config_repo = AZURE_DOCS_REPOS.get(repo_keyname)
    if config_repo:
        return config_repo

    log.debug("Unknown repository: building a synthetic configuration")
    return {
        "name": repo_keyname,
        "display_name": repo_keyname,
        "owner": repo_owner,
        "repository": repo_name,
        "articles_folder": "/",
        "icon": "",
    }


def resolve_since(raw_value: str) -> int:
    """Clamp a user supplied look-back window to a supported value.

    Args:
        raw_value (str): raw ``since`` query string parameter, may be None.

    Returns:
        int: a number of days between 1 and ``MAX_SINCE``.
    """
    if raw_value is None:
        return SINCE
    try:
        since = int(raw_value)
    except (TypeError, ValueError):
        log.debug("Ignoring invalid since value: %r", raw_value)
        return SINCE
    return max(1, min(since, MAX_SINCE))
