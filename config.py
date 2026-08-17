"""Manage the application configuration."""

import os

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
GITHUB_WEB_BASE = os.getenv("GITHUB_WEB_BASE", "https://github.com").rstrip("/")
GITHUB_API_BASE = os.getenv("GITHUB_API_BASE", "https://api.github.com").rstrip("/")
HTTP_TIMEOUT = int(os.getenv("AZDOCSWATCH_HTTP_TIMEOUT", 10))
USER_AGENT = os.getenv(
    "AZDOCSWATCH_USER_AGENT",
    "azure-docs-watcher (+https://github.com/lrivallain/azure_docs_watcher)",
)

# Azure Docs repo configuration

AZURE_DOCS_REPOS = {
    "MicrosoftDocs/azure-docs": {
        "name": "MicrosoftDocs/azure-docs",
        "display_name": "Azure Docs",
        "owner": "MicrosoftDocs",
        "repository": "azure-docs",
        "articles_folder": "/articles/",
        "icon": "azure-icons/Azure.svg",
    },
    "MicrosoftDocs/azure-sql": {
        "name": "MicrosoftDocs/azure-sql",
        "display_name": "Azure SQL",
        "owner": "MicrosoftDocs",
        "repository": "sql-docs",
        "articles_folder": "/azure-sql/",
        "icon": "azure-icons/Azure-SQL.svg",
    },
    "MicrosoftDocs/azure-quantum": {
        "name": "MicrosoftDocs/azure-quantum",
        "display_name": "Azure Quantum (preview)",
        "owner": "MicrosoftDocs",
        "repository": "quantum-docs",
        "articles_folder": "/articles/",
        "icon": "azure-icons/Azure-Quantum.svg",
    },
    "Azure/iotedge": {
        "name": "Azure/iotedge",
        "display_name": "Azure IoT Edge",
        "owner": "Azure",
        "repository": "iotedge",
        "articles_folder": "/doc/",
        "icon": "azure-icons/IoT-Edge.svg",
    },
    "lrivallain/azure_docs_watcher": {
        "name": "lrivallain/azure_docs_watcher",
        "display_name": "Azure Docs Watcher",
        "owner": "lrivallain",
        "repository": "azure_docs_watcher",
        "articles_folder": "",
        "icon": "favicon.svg",
    },
}
