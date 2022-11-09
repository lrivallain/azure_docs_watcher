import logging
import secrets
import os

from flask import Flask, redirect, session, url_for, send_from_directory
from cachetools import cached

app = Flask(__name__, static_folder="static")
app.secret_key = secrets.token_hex()

# Import local configuration
from config import *
from utils import cache

# configure logging
log = logging.getLogger(__name__)


from flask_dance.contrib.github import make_github_blueprint

# configure the gh-based login manager
blueprint = make_github_blueprint(
    client_id=GITHUB_CLIENT_ID, client_secret=GITHUB_CLIENT_SECRET
)
app.register_blueprint(blueprint, url_prefix="/login")


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
