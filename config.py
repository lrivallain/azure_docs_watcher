"""Manage the application configuration.
"""

import os


# Performances limits
SINCE = os.getenv("AZDOCSWATCH_SINCE", 5)
MAX_COMMITS = os.getenv("AZDOCSWATCH_MAX_COMMITS", 20)

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
