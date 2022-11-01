"""Main module."""

import os
import datetime
import logging
import secrets
from functools import wraps
from markupsafe import escape

from flask import (
    Flask,
    render_template,
    Response,
    request,
    redirect,
    url_for,
    session,
    g,
)
import coloredlogs
from github import Github, Repository
from github import UnknownObjectException, RateLimitExceededException
from flask_dance.contrib.github import make_github_blueprint, github as gh_auth

# Import local configuration
from config import *

# configure logging
log = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# create the Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex()
if app.debug:
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    coloredlogs.install(level="DEBUG")
else:
    coloredlogs.install(level="INFO")

# configure the gh-based login manager
blueprint = make_github_blueprint(
    client_id=GITHUB_CLIENT_ID, client_secret=GITHUB_CLIENT_SECRET
)
app.register_blueprint(blueprint, url_prefix="/login")


def login_suggested(f):
    """Decorator to manage the GitHub login suggestion to bypass performance limits.

    Args:
        f (_type_): function to decorate

    Returns:
        function: decorated function
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        log.debug("Checking if user is authenticated")
        g.using_shared_gh = True
        if not gh_auth.authorized:
            g.gh_token = GITHUB_ACCESS_TOKEN
        else:
            resp = gh_auth.get("/user")
            if not resp.json().get("login"):
                log.warn("User used to be authenticated but is not anymore")
                return redirect(url_for("github.login"))
            log.debug("User is authenticated")
            session["username"] = resp.json()["login"]
            g.gh_token = gh_auth.token.get("access_token")
            g.using_shared_gh = False
        g.gh = Github(g.gh_token)
        return f(*args, **kwargs)

    return decorated_function


@app.route("/login")
def login():
    """Login route.

    Redirects to GitHub login page.
    """
    return redirect(url_for("github.login"))


@app.route("/logout")
def logout():
    """Logout route: remove session data.

    Warning: the GitHub token is not revoked !

    Returns:
        flask.redirect: Redirect to the home page
    """
    session.clear()
    return redirect(url_for("home"))


@app.route("/")
@login_suggested
def home():
    """List files and folders to get commits logs from.

    Returns:
        str: html page
    """
    log.debug("Looking for repository %s/%s", AZURE_DOCS_OWNER, AZURE_DOCS_REPO)
    try:
        repo = g.gh.get_repo(f"{AZURE_DOCS_OWNER}/{AZURE_DOCS_REPO}")
    except UnknownObjectException:
        return Response("Repository not found", status=404)
    except RateLimitExceededException:
        return Response("Rate limit exceeded", status=429)
    except Exception as e:
        log.error(e)
        return Response("Error while listing files and folders", status=500)
    log.debug("Listing files and folders in %s", AZURE_DOCS_ARTICLES_FOLDER_PREFIX)
    try:
        contents = repo.get_dir_contents(
            AZURE_DOCS_ARTICLES_FOLDER_PREFIX.lstrip("/").rstrip("/")
        )
    except RateLimitExceededException:
        return Response("Rate limit exceeded", status=429)
    except Exception as e:
        log.error(e)
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
@login_suggested
def track(folder: str):
    """Track a folder in a repository

    Args:
        folder (str): folder to track

    Returns:
        str: html page
    """
    _since = int(request.args.get("since", SINCE))
    log.debug("Looking for repository %s/%s", AZURE_DOCS_OWNER, AZURE_DOCS_REPO)
    if not folder:
        return Response("Missing folder or file to like for changes", status=400)
    try:
        repo = g.gh.get_repo(f"{AZURE_DOCS_OWNER}/{AZURE_DOCS_REPO}")
    except UnknownObjectException:
        return Response("Repository not found", status=404)
    except Exception as e:
        log.error(e)
        return Response("Error while listing commits", status=500)

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
            if commits.totalCount > MAX_COMMITS and g.using_shared_gh:
                log.info(
                    "Using shared Github client: limiting commits to %s", MAX_COMMITS
                )
                commits = commits[:MAX_COMMITS]
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
        since=_since,
    )


@app.route("/favicon.svg")
def favicon():
    """Serve the favicon.

    Returns:
        flask.send_from_directory: favicon served by Flask.
    """
    return send_from_directory(
        os.path.join(app.root_path, "static"), "favicon.svg", mimetype="image/svg+xml"
    )


if __name__ == "__main__":
    app.run()
