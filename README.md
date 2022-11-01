# [Azure Docs changes watcher](https://azdocswatch.vupti.me)

Watch changes in the Azure docs repository.

* Free software: MIT license

# Features

* List Azure docs articles
* See the last changes in the Azure docs repository for a specific service/section.
* Use a GitHub oAuth token to increase the rate limit and the number of results.

# Known issues

## SAML enforcement policies

Some user within organizations with SAML enforcement policies may have issues with the GitHub oAuth login.

To workaround this issue, you can access directly to GitHub and ensure you are logged in against your organization account.
Then, you can access to the Azure Docs changes watcher and you should be able to login.
