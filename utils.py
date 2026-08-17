"""Helpers shared by the views."""

import logging

from config import AZURE_DOCS_REPOS

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
