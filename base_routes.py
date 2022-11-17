import logging
import secrets
import os

from flask import (
    Flask,
    redirect,
    session,
    request,
    url_for,
    send_from_directory,
    render_template,
)
from werkzeug.exceptions import HTTPException
from cachetools import cached

app = Flask(__name__, static_folder="static")
app.url_map.strict_slashes = False
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

    Returns:
        flask.redirect: Redirect to the GitHub login page
    """
    session["next"] = request.referrer
    return redirect(url_for("github.login"))


@app.route("/logout")
def logout():
    """Logout route: remove session data.

    Warning: the GitHub token is not revoked !

    Returns:
        flask.redirect: Redirect to the home page
    """
    session.clear()
    session["next"] = request.referrer
    return redirect(url_for("home"))


# Issue: #21 : favicon for RSS feed
@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )
