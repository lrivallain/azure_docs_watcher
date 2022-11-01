"""Main module."""

import os
import datetime
from markupsafe import escape
import logging

from flask import Flask, render_template, Response, request
from github import Github, Repository
from github import UnknownObjectException, RateLimitExceededException
import coloredlogs

# configuration
SINCE = os.environ.get("AZDOCSWATCH_SINCE", 5)
MAX_COMMITS = os.environ.get("AZDOCSWATCH_SINCE", 20)
AZURE_DOCS_REPO = "azure-docs"
AZURE_DOCS_OWNER = "MicrosoftDocs"
AZURE_DOCS_ARTICLES_FOLDER_PREFIX = "/articles/"

# configure logging
log = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# create the Flask app
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
if app.debug:
    coloredlogs.install(level="DEBUG")
else:
    coloredlogs.install(level="INFO")

# create the Github client
if not os.environ.get("GITHUB_ACCESS_TOKEN"):
    raise Exception("GITHUB_ACCESS_TOKEN environment variable is not set")
g = Github(os.environ.get("GITHUB_ACCESS_TOKEN"))


@app.route("/")
def home():
    """List files and folders to get commits logs from.

    Returns:
        str: html page
    """
    log.debug("Looking for repository %s/%s", AZURE_DOCS_OWNER, AZURE_DOCS_REPO)
    try:
        repo = g.get_repo(f"{AZURE_DOCS_OWNER}/{AZURE_DOCS_REPO}")
    except UnknownObjectException:
        return Response("Repository not found", status=404)
    except RateLimitExceededException:
        return Response("Rate limit exceeded", status=429)

    log.debug("Listing files and folders in %s", AZURE_DOCS_ARTICLES_FOLDER_PREFIX)
    try:
        contents = repo.get_dir_contents(
            AZURE_DOCS_ARTICLES_FOLDER_PREFIX.lstrip("/").rstrip("/")
        )
    except RateLimitExceededException:
        return Response("Rate limit exceeded", status=429)
    except:
        return Response("Error while listing files and folders", status=500)
    return render_template(
        "index.html",
        owner=escape(AZURE_DOCS_OWNER),
        repository=escape(AZURE_DOCS_REPO),
        contents=contents,
        since=SINCE,
        max_commits=MAX_COMMITS,
    )


@app.route(f"/{AZURE_DOCS_ARTICLES_FOLDER_PREFIX}<path:folder>")
# @app.errorhandler(400)
def track(folder: str):
    """Track a folder in a repository

    Args:
        folder (str): folder to track

    Returns:
        str: html page
    """
    _max_commits = int(request.args.get("max_commits", MAX_COMMITS))
    _since = int(request.args.get("since", SINCE))
    log.debug("Looking for repository %s/%s", AZURE_DOCS_OWNER, AZURE_DOCS_REPO)
    if not folder:
        return Response("Missing folder or file to like for changes", status=400)
    try:
        repo = g.get_repo(f"{AZURE_DOCS_OWNER}/{AZURE_DOCS_REPO}")
    except UnknownObjectException:
        return Response("Repository not found", status=404)

    log.debug("Calculating the reference date")
    tod = datetime.datetime.now()
    delta_since = datetime.timedelta(days=_since)
    ref_date = tod - delta_since

    _folder_path = os.path.join(AZURE_DOCS_ARTICLES_FOLDER_PREFIX, folder)

    try:
        commits = repo.get_commits(path=_folder_path, since=ref_date, until=tod)

        log.debug(f"{commits.totalCount} commits found in the last {_since} days")
        _commits = []
        if commits.totalCount > 0:
            if commits.totalCount > _max_commits:
                commits = commits[:_max_commits]
            for commit in commits:
                _commits.append(
                    {
                        "sha": escape(commit.sha[:7]),
                        "author": escape(commit.author.name),
                        "commit": escape(commit.commit),
                        "url": escape(commit.html_url),
                        "message": escape(commit.commit.message),
                        "date": escape(commit.commit.author.date),
                    }
                )
    except RateLimitExceededException:
        return Response("Rate limit exceeded", status=429)
    except Exception as e:
        log.error(e)
        return Response("Error while listing commits", status=500)

    return render_template(
        "commits.html",
        owner=escape(AZURE_DOCS_OWNER),
        repository=escape(AZURE_DOCS_REPO),
        folder=escape(_folder_path),
        commits=_commits,
        max_commits=MAX_COMMITS,
        since=SINCE,
    )


@app.route("/favicon.svg")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"), "favicon.svg", mimetype="image/svg+xml"
    )


if __name__ == "__main__":
    app.run()
