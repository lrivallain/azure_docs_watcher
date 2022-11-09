"""Manage the application configuration.
"""

import os

# App details
APP_AUTHOR = "Ludovic Rivallain"
APP_AUTHOR_EMAIL = "ludovic . rivallain @ gmail . com"
APP_DESCRIPTION = "Track changes in __repo__ documentation articles"

# Performances limits
SINCE = int(os.getenv("AZDOCSWATCH_SINCE", 5))
MAX_COMMITS = int(os.getenv("AZDOCSWATCH_MAX_COMMITS", 20))

# Cache configuration
CACHE_SIZE = int(os.getenv("AZDOCSWATCH_CACHE_SIZE", 1024))
CACHE_TTL = int(os.getenv("AZDOCSWATCH_CACHE_TTL", 600))

# GitHub application configuration
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

# Azure Docs repo configuration
AZURE_DOCS_REPO = "azure-docs"
AZURE_DOCS_OWNER = "MicrosoftDocs"
AZURE_DOCS_ARTICLES_FOLDER_PREFIX = "/articles/"

# Shared Github client token
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
if not GITHUB_ACCESS_TOKEN:
    raise Exception("GITHUB_ACCESS_TOKEN environment variable is not set")

AZURE_DOCS_REPOS = {
    "azure-docs": {
        "name": "azure-docs",
        "display_name": "Azure Docs",
        "owner": "MicrosoftDocs",
        "repository": "azure-docs",
        "articles_folder": "/articles/",
        "icon": "azure-icons/Azure.svg",
    },
    "azure-sql": {
        "name": "azure-sql",
        "display_name": "Azure SQL",
        "owner": "MicrosoftDocs",
        "repository": "sql-docs",
        "articles_folder": "/azure-sql/",
        "icon": "azure-icons/Azure-SQL.svg",
    },
    "azure-quantum": {
        "name": "azure-quantum",
        "display_name": "Azure Quantum (preview)",
        "owner": "MicrosoftDocs",
        "repository": "quantum-docs",
        "articles_folder": "/articles/",
        "icon": "azure-icons/Azure-Quantum.svg",
    },
    "azure_docs_watcher": {
        "name": "azure_docs_watcher",
        "display_name": "Azure Docs Watcher",
        "owner": "lrivallain",
        "repository": "azure_docs_watcher",
        "articles_folder": "",
        "icon": "favicon.svg",
    },
}
