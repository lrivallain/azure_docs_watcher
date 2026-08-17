"""Tests for the credential-free GitHub client."""

import pytest
import requests
import responses
from conftest import atom_entry, atom_feed, days_ago

import github_client
from errors import GitHubError

BRANCH_URL = "https://github.com/MicrosoftDocs/azure-docs/commits.atom"
FEED_URL = "https://github.com/MicrosoftDocs/azure-docs/commits/main/articles/aks.atom"
ROOT_FEED_URL = "https://github.com/MicrosoftDocs/azure-docs/commits/main.atom"
CONTENTS_URL = "https://api.github.com/repos/MicrosoftDocs/azure-docs/contents/articles"


def register_branch(branch: str = "main"):
    """Register the branch discovery feed.

    Args:
        branch (str): the default branch to advertise.
    """
    responses.add(
        responses.GET,
        BRANCH_URL,
        body=atom_feed(title=f"Recent Commits to azure-docs:{branch}"),
        status=200,
    )


@responses.activate
def test_default_branch_is_read_from_the_feed_title():
    register_branch("live")
    assert github_client.get_default_branch("MicrosoftDocs", "azure-docs") == "live"


@responses.activate
def test_default_branch_is_cached():
    register_branch()
    github_client.get_default_branch("MicrosoftDocs", "azure-docs")
    github_client.get_default_branch("MicrosoftDocs", "azure-docs")
    assert len(responses.calls) == 1


@responses.activate
def test_default_branch_rejects_an_unexpected_title():
    responses.add(responses.GET, BRANCH_URL, body=atom_feed(title="Nope"), status=200)
    with pytest.raises(GitHubError) as excinfo:
        github_client.get_default_branch("MicrosoftDocs", "azure-docs")
    assert excinfo.value.status_code == 502


@responses.activate
def test_commits_are_parsed_from_the_feed():
    register_branch()
    responses.add(
        responses.GET,
        FEED_URL,
        body=atom_feed(atom_entry(sha="b" * 40, message="Fix a typo", name="alice")),
        status=200,
    )
    commits = github_client.get_commits("MicrosoftDocs", "azure-docs", "articles/aks")
    assert len(commits) == 1
    assert commits[0]["sha"] == "b" * 40
    assert commits[0]["author"] == "alice"
    assert commits[0]["message"] == "Fix a typo"
    assert commits[0]["url"].endswith("b" * 40)
    assert commits[0]["date"].tzinfo is not None


@responses.activate
def test_multiline_message_is_taken_from_the_content_not_the_title():
    register_branch()
    message = "Merge pull request #1\n\nCo-authored-by: bot <bot@example.com>"
    responses.add(
        responses.GET, FEED_URL, body=atom_feed(atom_entry(message=message)), status=200
    )
    commits = github_client.get_commits("MicrosoftDocs", "azure-docs", "articles/aks")
    # The <pre> content is HTML escaped by GitHub and must be unescaped once.
    assert commits[0]["message"] == message


@responses.activate
def test_author_falls_back_to_the_email_local_part():
    register_branch()
    responses.add(
        responses.GET,
        FEED_URL,
        body=atom_feed(atom_entry(name="", email="ghost@example.com")),
        status=200,
    )
    commits = github_client.get_commits("MicrosoftDocs", "azure-docs", "articles/aks")
    assert commits[0]["author"] == "ghost"


@responses.activate
def test_old_commits_are_still_returned():
    # The feed holds at most 20 entries and cannot be paginated, so filtering
    # them by date could only ever hide history: a quiet section must still
    # show when it last changed.
    register_branch()
    responses.add(
        responses.GET,
        FEED_URL,
        body=atom_feed(
            atom_entry(sha="c" * 40, updated=days_ago(1))
            + atom_entry(sha="d" * 40, updated=days_ago(900))
        ),
        status=200,
    )
    commits = github_client.get_commits("MicrosoftDocs", "azure-docs", "articles/aks")
    assert [commit["sha"] for commit in commits] == ["c" * 40, "d" * 40]


@responses.activate
def test_commits_are_returned_most_recent_first():
    register_branch()
    responses.add(
        responses.GET,
        FEED_URL,
        body=atom_feed(
            atom_entry(sha="e" * 40, updated=days_ago(3))
            + atom_entry(sha="f" * 40, updated=days_ago(1))
        ),
        status=200,
    )
    commits = github_client.get_commits("MicrosoftDocs", "azure-docs", "articles/aks")
    assert [commit["sha"] for commit in commits] == ["f" * 40, "e" * 40]


@responses.activate
def test_every_feed_entry_is_returned():
    # GitHub caps the feed itself, so nothing is truncated on our side.
    register_branch()
    entries = "".join(atom_entry(sha=f"{index:040d}") for index in range(20))
    responses.add(responses.GET, FEED_URL, body=atom_feed(entries), status=200)
    commits = github_client.get_commits("MicrosoftDocs", "azure-docs", "articles/aks")
    assert len(commits) == 20


@responses.activate
def test_the_feed_is_fetched_once_for_repeated_calls():
    register_branch()
    responses.add(responses.GET, FEED_URL, body=atom_feed(atom_entry()), status=200)
    github_client.get_commits("MicrosoftDocs", "azure-docs", "articles/aks")
    github_client.get_commits("MicrosoftDocs", "azure-docs", "articles/aks")
    # One branch lookup and one feed fetch, shared by both calls.
    assert len(responses.calls) == 2


@responses.activate
def test_an_empty_path_targets_the_repository_root():
    register_branch()
    responses.add(responses.GET, ROOT_FEED_URL, body=atom_feed(atom_entry()), status=200)
    commits = github_client.get_commits("MicrosoftDocs", "azure-docs", "")
    assert len(commits) == 1


@responses.activate
def test_a_missing_path_is_reported_as_a_404():
    register_branch()
    responses.add(responses.GET, FEED_URL, body="Not Found", status=404)
    with pytest.raises(GitHubError) as excinfo:
        github_client.get_commits("MicrosoftDocs", "azure-docs", "articles/aks")
    assert excinfo.value.status_code == 404


@responses.activate
def test_rate_limiting_produces_an_actionable_message():
    responses.add(
        responses.GET,
        CONTENTS_URL,
        json={"message": "API rate limit exceeded for 1.2.3.4."},
        status=403,
    )
    with pytest.raises(GitHubError) as excinfo:
        github_client.get_directory("MicrosoftDocs", "azure-docs", "articles")
    assert excinfo.value.status_code == 403
    assert "rate limiting" in excinfo.value.message


@responses.activate
def test_directory_lists_folders_first_then_files():
    responses.add(
        responses.GET,
        CONTENTS_URL,
        json=[
            {"name": "readme.md", "path": "articles/readme.md", "type": "file"},
            {"name": "storage", "path": "articles/storage", "type": "dir"},
            {"name": "aks", "path": "articles/aks", "type": "dir"},
        ],
        status=200,
    )
    entries = github_client.get_directory("MicrosoftDocs", "azure-docs", "articles")
    assert [entry["name"] for entry in entries] == ["aks", "storage", "readme.md"]


@responses.activate
def test_a_file_path_is_not_a_directory():
    responses.add(
        responses.GET,
        CONTENTS_URL,
        json={"name": "readme.md", "type": "file"},
        status=200,
    )
    with pytest.raises(GitHubError) as excinfo:
        github_client.get_directory("MicrosoftDocs", "azure-docs", "articles")
    assert excinfo.value.status_code == 404


@responses.activate
def test_no_credential_is_ever_sent():
    register_branch()
    responses.add(responses.GET, FEED_URL, body=atom_feed(atom_entry()), status=200)
    github_client.get_commits("MicrosoftDocs", "azure-docs", "articles/aks")
    for call in responses.calls:
        assert "Authorization" not in call.request.headers


@responses.activate
def test_a_timeout_is_reported_as_a_gateway_timeout():
    responses.add(responses.GET, BRANCH_URL, body=requests.exceptions.Timeout())
    with pytest.raises(GitHubError) as excinfo:
        github_client.get_default_branch("MicrosoftDocs", "azure-docs")
    assert excinfo.value.status_code == 504


@responses.activate
def test_a_connection_failure_is_reported_as_a_bad_gateway():
    responses.add(responses.GET, BRANCH_URL, body=requests.exceptions.ConnectionError())
    with pytest.raises(GitHubError) as excinfo:
        github_client.get_default_branch("MicrosoftDocs", "azure-docs")
    assert excinfo.value.status_code == 502


@responses.activate
def test_a_low_level_os_error_does_not_escape():
    # A broken CA bundle raises a plain OSError, which is not a
    # requests.exceptions.RequestException and used to surface as a 500.
    responses.add(
        responses.GET,
        BRANCH_URL,
        body=OSError("Could not find a suitable TLS CA certificate bundle"),
    )
    with pytest.raises(GitHubError) as excinfo:
        github_client.get_default_branch("MicrosoftDocs", "azure-docs")
    assert excinfo.value.status_code == 502
