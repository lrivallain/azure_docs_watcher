"""Shared test fixtures."""

import datetime
import html

import pytest

import github_client


def atom_feed(entries: str = "", title: str = "Recent Commits to azure-docs:main") -> str:
    """Build an Atom commit feed similar to the ones served by GitHub.

    Args:
        entries (str): the serialized ``<entry>`` elements.
        title (str): the feed title, advertising the default branch.

    Returns:
        str: the Atom document.
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">
  <title>{title}</title>
  {entries}
</feed>"""


def atom_entry(
    sha: str = "a" * 40,
    message: str = "Update the docs",
    name: str = "octocat",
    email: str = "octocat@example.com",
    updated: str = None,
) -> str:
    """Build a single Atom commit entry, escaped the way GitHub escapes them.

    GitHub wraps the commit message in an HTML ``<pre>`` block, which is itself
    serialized as the text of an XML element: the message is therefore escaped
    twice.

    Args:
        sha (str): the commit sha.
        message (str): the commit message, unescaped.
        name (str): the commit author name, may be empty.
        email (str): the commit author email.
        updated (str): the commit date, defaults to now.

    Returns:
        str: the serialized ``<entry>`` element.
    """
    if updated is None:
        updated = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    first_line = message.splitlines()[0]
    block = f"<pre style='white-space:pre-wrap;width:81ex'>{html.escape(message)}</pre>"
    return f"""<entry>
    <id>tag:github.com,2008:Grit::Commit/{sha}</id>
    <link type="text/html" rel="alternate"
      href="https://github.com/MicrosoftDocs/azure-docs/commit/{sha}"/>
    <title>
        {html.escape(first_line)}
    </title>
    <updated>{updated}</updated>
    <author><name>{html.escape(name)}</name><email>{html.escape(email)}</email></author>
    <content type="html">
      {html.escape(block)}
    </content>
  </entry>"""


def days_ago(days: int) -> str:
    """Build an Atom timestamp placed a number of days in the past.

    Args:
        days (int): how many days back.

    Returns:
        str: an ISO-8601 timestamp.
    """
    moment = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture(autouse=True)
def clear_caches():
    """Clear the module level caches so tests cannot leak into each other."""
    github_client._branch_cache.clear()
    github_client._feed_cache.clear()
    github_client._directory_cache.clear()
    yield
    github_client._branch_cache.clear()
    github_client._feed_cache.clear()
    github_client._directory_cache.clear()


@pytest.fixture
def client():
    """Provide a Flask test client.

    Returns:
        flask.testing.FlaskClient: the test client.
    """
    from app import app

    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client
