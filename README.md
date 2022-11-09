<img src="/static/favicon.svg" width="250">

# [Azure Docs changes watcher](https://azdocswatch.vupti.me)

Watch changes in the Azure docs repository.

* Free software: MIT license

# Features

* List Azure docs articles for some repositories:
  * [Azure Docs](https://github.com/MicrosoftDocs/azure-docs)
  * [Azure SQL](https://github.com/MicrosoftDocs/sql-docs)
  * [Azure Quantum](https://github.com/MicrosoftDocs/quantum-docs)
* See the last changes in the Azure docs repository for a specific service/section
* Use a GitHub oAuth token to increase the rate limit and the number of results
* RSS feed for each section (#7)
* Cache capabilities are used to reduce the number of API calls to GitHub and improve performance (#9)

# Known issues

## #10 - SAML enforcement policies

Some user within organizations with SAML enforcement policies may have issues with the GitHub oAuth login.

To workaround this issue, you can access directly to GitHub and ensure you are logged in against your organization account.
Then, you can access to the Azure Docs changes watcher and you should be able to login.
