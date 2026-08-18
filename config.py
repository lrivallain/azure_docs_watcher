"""Manage the application configuration."""

import logging
import os

log = logging.getLogger(__name__)

# App details
APP_AUTHOR = "Ludovic Rivallain"
APP_AUTHOR_EMAIL = "ludovic . rivallain @ gmail . com"
APP_DESCRIPTION = "Track changes in __repo__ documentation articles"

# GitHub serves commit Atom feeds as a single, non paginated page of this many
# entries, with no date filter. Nothing can raise that ceiling, so it is not
# configurable: it only serves to tell visitors when a listing is capped.
ATOM_FEED_SIZE = 20

# Cache configuration
CACHE_SIZE = int(os.getenv("AZDOCSWATCH_CACHE_SIZE", 1024))
CACHE_TTL = int(os.getenv("AZDOCSWATCH_CACHE_TTL", 600))

# GitHub endpoints and HTTP client settings
GITHUB_WEB_BASE = "https://github.com"
GITHUB_API_BASE = "https://api.github.com"
HTTP_TIMEOUT = int(os.getenv("AZDOCSWATCH_HTTP_TIMEOUT", 10))
USER_AGENT = os.getenv(
    "AZDOCSWATCH_USER_AGENT",
    "azure-docs-watcher (+https://github.com/lrivallain/azure_docs_watcher)",
)

# Watched repositories.
#
# Declaration order drives the order of the home page: the most broadly useful
# products come first, niche and edge ones last. Microsoft has been splitting
# MicrosoftDocs/azure-docs into per-domain repositories, so several services
# that used to live there are watched through their own repository below.
AZURE_DOCS_REPOS = {
    # Core Azure platform
    "MicrosoftDocs/azure-docs": {
        "name": "MicrosoftDocs/azure-docs",
        "display_name": "Azure Docs",
        "owner": "MicrosoftDocs",
        "repository": "azure-docs",
        "articles_folder": "/articles/",
        "icon": "azure-icons/Azure.svg",
    },
    "MicrosoftDocs/azure-compute-docs": {
        "name": "MicrosoftDocs/azure-compute-docs",
        "display_name": "Azure Compute",
        "owner": "MicrosoftDocs",
        "repository": "azure-compute-docs",
        "articles_folder": "/articles/",
        "glyph": "cpu",
    },
    "MicrosoftDocs/azure-aks-docs": {
        "name": "MicrosoftDocs/azure-aks-docs",
        "display_name": "Azure Kubernetes Service",
        "owner": "MicrosoftDocs",
        "repository": "azure-aks-docs",
        "articles_folder": "/articles/",
        "glyph": "boxes",
    },
    "MicrosoftDocs/azure-databases-docs": {
        "name": "MicrosoftDocs/azure-databases-docs",
        "display_name": "Azure Databases",
        "owner": "MicrosoftDocs",
        "repository": "azure-databases-docs",
        "articles_folder": "/articles/",
        "glyph": "database",
    },
    "MicrosoftDocs/azure-sql": {
        "name": "MicrosoftDocs/azure-sql",
        "display_name": "Azure SQL",
        "owner": "MicrosoftDocs",
        "repository": "sql-docs",
        "articles_folder": "/azure-sql/",
        "icon": "azure-icons/Azure-SQL.svg",
    },
    # AI and data
    "MicrosoftDocs/azure-ai-docs": {
        "name": "MicrosoftDocs/azure-ai-docs",
        "display_name": "Azure AI and Foundry",
        "owner": "MicrosoftDocs",
        "repository": "azure-ai-docs",
        "articles_folder": "/articles/",
        "glyph": "robot",
    },
    "MicrosoftDocs/fabric-docs": {
        "name": "MicrosoftDocs/fabric-docs",
        "display_name": "Microsoft Fabric",
        "owner": "MicrosoftDocs",
        "repository": "fabric-docs",
        "articles_folder": "/docs/",
        "glyph": "diagram-3",
    },
    # Identity, security and operations
    "MicrosoftDocs/entra-docs": {
        "name": "MicrosoftDocs/entra-docs",
        "display_name": "Microsoft Entra",
        "owner": "MicrosoftDocs",
        "repository": "entra-docs",
        "articles_folder": "/docs/",
        "glyph": "person-badge",
    },
    "MicrosoftDocs/defender-docs": {
        "name": "MicrosoftDocs/defender-docs",
        "display_name": "Microsoft Defender and Sentinel",
        "owner": "MicrosoftDocs",
        "repository": "defender-docs",
        # The products sit directly at the root of this repository.
        "articles_folder": "/",
        "glyph": "shield-check",
    },
    "MicrosoftDocs/azure-security-docs": {
        "name": "MicrosoftDocs/azure-security-docs",
        "display_name": "Azure Security",
        "owner": "MicrosoftDocs",
        "repository": "azure-security-docs",
        "articles_folder": "/articles/",
        "glyph": "shield-lock",
    },
    "MicrosoftDocs/azure-monitor-docs": {
        "name": "MicrosoftDocs/azure-monitor-docs",
        "display_name": "Azure Monitor",
        "owner": "MicrosoftDocs",
        "repository": "azure-monitor-docs",
        "articles_folder": "/articles/",
        "glyph": "graph-up-arrow",
    },
    # Guidance
    "MicrosoftDocs/architecture-center": {
        "name": "MicrosoftDocs/architecture-center",
        "display_name": "Azure Architecture Center",
        "owner": "MicrosoftDocs",
        "repository": "architecture-center",
        "articles_folder": "/docs/",
        "glyph": "compass",
    },
    "MicrosoftDocs/cloud-adoption-framework": {
        "name": "MicrosoftDocs/cloud-adoption-framework",
        "display_name": "Cloud Adoption Framework",
        "owner": "MicrosoftDocs",
        "repository": "cloud-adoption-framework",
        "articles_folder": "/docs/",
        "glyph": "map",
    },
    # Developer and platform tooling
    "MicrosoftDocs/azure-dev-docs": {
        "name": "MicrosoftDocs/azure-dev-docs",
        "display_name": "Azure for Developers",
        "owner": "MicrosoftDocs",
        "repository": "azure-dev-docs",
        "articles_folder": "/articles/",
        "glyph": "code-slash",
    },
    "MicrosoftDocs/azure-devops-docs": {
        "name": "MicrosoftDocs/azure-devops-docs",
        "display_name": "Azure DevOps",
        "owner": "MicrosoftDocs",
        "repository": "azure-devops-docs",
        "articles_folder": "/docs/",
        "glyph": "infinity",
    },
    # Endpoint, hybrid and edge
    "MicrosoftDocs/memdocs": {
        "name": "MicrosoftDocs/memdocs",
        "display_name": "Microsoft Intune",
        "owner": "MicrosoftDocs",
        "repository": "memdocs",
        "articles_folder": "/intune/",
        "glyph": "phone",
    },
    "MicrosoftDocs/azure-stack-docs": {
        "name": "MicrosoftDocs/azure-stack-docs",
        "display_name": "Azure Local",
        "owner": "MicrosoftDocs",
        "repository": "azure-stack-docs",
        "articles_folder": "/azure-local/",
        "glyph": "hdd-stack",
    },
    "Azure/iotedge": {
        "name": "Azure/iotedge",
        "display_name": "Azure IoT Edge",
        "owner": "Azure",
        "repository": "iotedge",
        "articles_folder": "/doc/",
        "icon": "azure-icons/IoT-Edge.svg",
    },
    "MicrosoftDocs/azure-quantum": {
        "name": "MicrosoftDocs/azure-quantum",
        "display_name": "Azure Quantum",
        "owner": "MicrosoftDocs",
        "repository": "quantum-docs",
        "articles_folder": "/articles/",
        "icon": "azure-icons/Azure-Quantum.svg",
    },
    # This very application
    "lrivallain/azure_docs_watcher": {
        "name": "lrivallain/azure_docs_watcher",
        "display_name": "Azure Docs Watcher",
        "owner": "lrivallain",
        "repository": "azure_docs_watcher",
        "articles_folder": "",
        "icon": "favicon.svg",
    },
}


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
    config_repo = AZURE_DOCS_REPOS.get(repo_keyname)
    if config_repo:
        return config_repo

    log.debug("Unknown repository %s: building a synthetic configuration", repo_keyname)
    return {
        "name": repo_keyname,
        "display_name": repo_keyname,
        "owner": repo_owner,
        "repository": repo_name,
        "articles_folder": "/",
        "icon": "",
    }
