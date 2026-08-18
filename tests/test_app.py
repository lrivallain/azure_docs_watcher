"""Tests for the views."""

import responses
from conftest import atom_entry, atom_feed

BRANCH_URL = "https://github.com/MicrosoftDocs/azure-docs/commits.atom"
SECTION_FEED_URL = (
    "https://github.com/MicrosoftDocs/azure-docs/commits/main/articles/aks.atom"
)
CONTENTS_URL = "https://api.github.com/repos/MicrosoftDocs/azure-docs/contents/articles"


def register_section():
    """Register the upstream calls needed to render a section."""
    responses.add(
        responses.GET,
        BRANCH_URL,
        body=atom_feed(title="Recent Commits to azure-docs:main"),
        status=200,
    )
    responses.add(
        responses.GET,
        SECTION_FEED_URL,
        body=atom_feed(atom_entry(message="Update the AKS docs", name="alice")),
        status=200,
    )


def test_home_lists_the_curated_repositories(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"MicrosoftDocs/azure-docs" in response.data


def test_home_needs_no_upstream_call(client):
    # The home page is built from the configuration only.
    with responses.RequestsMock():
        assert client.get("/").status_code == 200


@responses.activate
def test_repo_home_lists_the_sections(client):
    responses.add(
        responses.GET,
        CONTENTS_URL,
        json=[{"name": "aks", "path": "articles/aks", "type": "dir"}],
        status=200,
    )
    response = client.get("/MicrosoftDocs/azure-docs")
    assert response.status_code == 200
    assert b"aks" in response.data


@responses.activate
def test_section_index_is_always_a_list(client):
    responses.add(
        responses.GET,
        CONTENTS_URL,
        json=[{"name": "aks", "path": "articles/aks", "type": "dir"}],
        status=200,
    )
    response = client.get("/MicrosoftDocs/azure-docs")
    # The layout is forced rather than read from local storage, and the switch
    # is not offered: a grid of sections would add nothing.
    assert b"'list'" in response.data
    assert b'data-view-choice="grid"' not in response.data
    assert b"section-card" in response.data


@responses.activate
def test_section_page_renders_the_commits(client):
    register_section()
    response = client.get("/MicrosoftDocs/azure-docs/aks")
    assert response.status_code == 200
    assert b"Update the AKS docs" in response.data
    assert b"alice" in response.data


@responses.activate
def test_section_page_advertises_its_feed(client):
    register_section()
    response = client.get("/MicrosoftDocs/azure-docs/aks")
    assert b'type="application/rss+xml"' in response.data
    assert b"/feed/MicrosoftDocs/azure-docs/aks" in response.data


def test_home_offers_the_layout_toggle(client):
    response = client.get("/")
    assert b'data-view-choice="grid"' in response.data
    assert b'data-view-choice="list"' in response.data
    assert b"view-collection" in response.data


@responses.activate
def test_action_buttons_carry_a_tooltip_title(client):
    register_section()
    response = client.get("/MicrosoftDocs/azure-docs/aks")
    # Tooltips are built from the title attribute, so a button without one is
    # silently left without a tooltip.
    assert b'title="View commit' in response.data

    home = client.get("/")
    assert b'title="Browse the sections of' in home.data


@responses.activate
def test_section_page_offers_the_layout_toggle(client):
    register_section()
    response = client.get("/MicrosoftDocs/azure-docs/aks")
    assert b'data-view-choice="grid"' in response.data
    assert b'data-view-choice="list"' in response.data
    assert b"view-collection" in response.data


@responses.activate
def test_feed_is_served_as_rss(client):
    register_section()
    response = client.get("/feed/MicrosoftDocs/azure-docs/aks")
    assert response.status_code == 200
    assert response.mimetype == "application/rss+xml"
    assert b"<rss" in response.data
    assert b"<dc:creator>alice</dc:creator>" in response.data


@responses.activate
def test_feed_points_back_to_the_html_page(client):
    register_section()
    response = client.get("/feed/MicrosoftDocs/azure-docs/aks")
    body = response.data.decode()
    assert "<link>http://localhost/MicrosoftDocs/azure-docs/aks</link>" in body
    assert 'rel="self"' in body


@responses.activate
def test_feed_carries_its_http_validators(client):
    register_section()
    response = client.get("/feed/MicrosoftDocs/azure-docs/aks")
    assert response.status_code == 200
    assert response.headers["ETag"]
    assert response.headers["Last-Modified"]
    assert response.cache_control.public
    assert response.cache_control.max_age


@responses.activate
def test_a_known_etag_gets_a_bodyless_304(client):
    register_section()
    first = client.get("/feed/MicrosoftDocs/azure-docs/aks")
    second = client.get(
        "/feed/MicrosoftDocs/azure-docs/aks",
        headers={"If-None-Match": first.headers["ETag"]},
    )
    assert second.status_code == 304
    assert second.data == b""
    # The validator must survive the 304, or the next poll cannot reuse it.
    assert second.headers["ETag"] == first.headers["ETag"]


@responses.activate
def test_an_up_to_date_reader_gets_a_304(client):
    register_section()
    first = client.get("/feed/MicrosoftDocs/azure-docs/aks")
    second = client.get(
        "/feed/MicrosoftDocs/azure-docs/aks",
        headers={"If-Modified-Since": first.headers["Last-Modified"]},
    )
    assert second.status_code == 304


@responses.activate
def test_the_etag_is_stable_across_polls(client):
    register_section()
    # An unstable ETag would make every poll a full download, which is exactly
    # what the cached body exists to prevent.
    first = client.get("/feed/MicrosoftDocs/azure-docs/aks")
    second = client.get("/feed/MicrosoftDocs/azure-docs/aks")
    assert first.headers["ETag"] == second.headers["ETag"]
    assert first.data == second.data


@responses.activate
def test_a_stale_etag_gets_the_new_body(client):
    register_section()
    response = client.get(
        "/feed/MicrosoftDocs/azure-docs/aks",
        headers={"If-None-Match": '"not-the-current-one"'},
    )
    assert response.status_code == 200
    assert b"<rss" in response.data


@responses.activate
def test_a_new_commit_changes_the_etag(client):
    import feeds
    import github_client

    register_section()
    first = client.get("/feed/MicrosoftDocs/azure-docs/aks")

    # Only the upstream commits change: the render cache must not mask that.
    github_client._feed_cache.clear()
    responses.add(
        responses.GET,
        SECTION_FEED_URL,
        body=atom_feed(
            atom_entry(sha="b" * 40, message="Another change", name="bob")
            + atom_entry(message="Update the AKS docs", name="alice")
        ),
        status=200,
    )
    second = client.get("/feed/MicrosoftDocs/azure-docs/aks")
    assert second.status_code == 200
    assert second.headers["ETag"] != first.headers["ETag"]
    assert b"bob" in second.data
    assert len(feeds._render_cache) == 2


@responses.activate
def test_api_returns_iso_dates(client):
    register_section()
    response = client.get("/api/MicrosoftDocs/azure-docs/aks")
    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload) == 1
    assert payload[0]["author"] == "alice"
    # ISO-8601, not the RFC 822 default of Flask.
    assert payload[0]["date"].count("-") >= 2
    assert "T" in payload[0]["date"]


@responses.activate
def test_a_legacy_since_parameter_is_ignored_rather_than_failing(client):
    register_section()
    # Old bookmarks and feed subscriptions still carry ?since=, which must not
    # break now that the whole feed is always returned.
    assert client.get("/MicrosoftDocs/azure-docs/aks?since=9999").status_code == 200
    assert client.get("/MicrosoftDocs/azure-docs/aks?since=abc").status_code == 200


@responses.activate
def test_a_missing_repository_renders_the_error_page(client):
    responses.add(responses.GET, CONTENTS_URL, json={"message": "Not Found"}, status=404)
    response = client.get("/MicrosoftDocs/azure-docs")
    assert response.status_code == 404
    assert b"Error: 404" in response.data


def test_unknown_route_renders_the_error_page(client):
    response = client.get("/this/is/not/a/valid/route/at/all")
    assert response.status_code in (404, 500)
