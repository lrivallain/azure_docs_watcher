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
    # Content progressively split out of MicrosoftDocs/azure-docs: those
    # services are no longer documented in the historical repository.
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
    "MicrosoftDocs/azure-ai-docs": {
        "name": "MicrosoftDocs/azure-ai-docs",
        "display_name": "Azure AI and Foundry",
        "owner": "MicrosoftDocs",
        "repository": "azure-ai-docs",
        "articles_folder": "/articles/",
        "glyph": "robot",
    },
    "MicrosoftDocs/azure-monitor-docs": {
        "name": "MicrosoftDocs/azure-monitor-docs",
        "display_name": "Azure Monitor",
        "owner": "MicrosoftDocs",
        "repository": "azure-monitor-docs",
        "articles_folder": "/articles/",
        "glyph": "graph-up-arrow",
    },
    "MicrosoftDocs/azure-security-docs": {
        "name": "MicrosoftDocs/azure-security-docs",
        "display_name": "Azure Security",
        "owner": "MicrosoftDocs",
        "repository": "azure-security-docs",
        "articles_folder": "/articles/",
        "glyph": "shield-lock",
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
    "MicrosoftDocs/entra-docs": {
        "name": "MicrosoftDocs/entra-docs",
        "display_name": "Microsoft Entra",
        "owner": "MicrosoftDocs",
        "repository": "entra-docs",
        "articles_folder": "/docs/",
        "glyph": "person-badge",
    },
    "MicrosoftDocs/fabric-docs": {
        "name": "MicrosoftDocs/fabric-docs",
        "display_name": "Microsoft Fabric",
        "owner": "MicrosoftDocs",
        "repository": "fabric-docs",
        "articles_folder": "/docs/",
        "glyph": "diagram-3",
    },
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
    "MicrosoftDocs/azure-dev-docs": {
        "name": "MicrosoftDocs/azure-dev-docs",
        "display_name": "Azure for Developers",
        "owner": "MicrosoftDocs",
        "repository": "azure-dev-docs",
        "articles_folder": "/articles/",
        "glyph": "code-slash",
    },
    "MicrosoftDocs/memdocs": {
        "name": "MicrosoftDocs/memdocs",
        "display_name": "Microsoft Intune",
        "owner": "MicrosoftDocs",
        "repository": "memdocs",
        "articles_folder": "/intune/",
        "glyph": "phone",
    },
    "MicrosoftDocs/azure-devops-docs": {
        "name": "MicrosoftDocs/azure-devops-docs",
        "display_name": "Azure DevOps",
        "owner": "MicrosoftDocs",
        "repository": "azure-devops-docs",
        "articles_folder": "/docs/",
        "glyph": "infinity",
    },
    "MicrosoftDocs/azure-stack-docs": {
        "name": "MicrosoftDocs/azure-stack-docs",
        "display_name": "Azure Local",
        "owner": "MicrosoftDocs",
        "repository": "azure-stack-docs",
        "articles_folder": "/azure-local/",
        "glyph": "hdd-stack",
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
