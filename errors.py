import logging

from flask import render_template
from werkzeug.exceptions import HTTPException

from base_routes import app


# configure logging
log = logging.getLogger(__name__)


@app.errorhandler(HTTPException)
def basic_error_handling(e):
    log.error(f"{e.code}: {str(e.description)}")
    return (
        render_template(
            "error.html",
            error_code=e.code,
            error_message=e.description,
        ),
        e.code,
    )


class SAML403(Exception):
    def __init__(self, repository):
        self.repository = repository


@app.errorhandler(SAML403)
def saml403(e):
    """Error handler for SAML403 exceptions.

    Args:
        e (SAML403): Exception

    Returns:
        flask.render_template: Error page
    """
    log.warning(f"SAML enforcement error. A specific error page is displayed.")
    log.debug(f"Repository: {e.repository.get('owner')}/{e.repository.get('name')}")
    return render_template("error_saml.html", repository=e.repository), 403
