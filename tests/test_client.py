import requests

from jira_metrics.config import JiraSettings
from jira_metrics.jira.client import JiraClient


def make_settings(**overrides) -> JiraSettings:
    defaults = dict(
        base_url="https://demo.atlassian.net",
        user="user@example.com",
        token="token",
        project="DEMO",
        labels=(),
        team_label=None,
        field_story_points="customfield_99001",
        field_sprint="customfield_99002",
        page_size=100,
    )
    defaults.update(overrides)
    return JiraSettings(**defaults)


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_search_issues_includes_configured_field_ids(monkeypatch, fixture):
    captured = {}

    def fake_post(url, headers, json, auth, timeout):
        captured["payload"] = json
        captured["timeout"] = timeout
        return FakeResponse({"issues": []})

    monkeypatch.setattr(requests, "post", fake_post)

    client = JiraClient(make_settings())
    client.search_issues('project = "DEMO"')

    assert "customfield_99001" in captured["payload"]["fields"]
    assert "customfield_99002" in captured["payload"]["fields"]
    assert captured["timeout"] == 30


def test_search_issues_paginates_via_next_page_token(monkeypatch, fixture):
    page1 = fixture("search_page1.json")
    page2 = fixture("search_page2.json")
    calls = []

    def fake_post(url, headers, json, auth, timeout):
        calls.append(json)
        if "nextPageToken" in json:
            return FakeResponse(page2)
        return FakeResponse(page1)

    monkeypatch.setattr(requests, "post", fake_post)

    client = JiraClient(make_settings())
    issues = client.search_issues('project = "DEMO"')

    assert [issue["key"] for issue in issues] == ["DEMO-1", "DEMO-2", "DEMO-3"]
    assert len(calls) == 2
    assert calls[1]["nextPageToken"] == "page-2-token"


def test_list_fields_returns_parsed_json(monkeypatch):
    captured = {}

    def fake_get(url, headers, auth, timeout):
        captured["url"] = url
        captured["timeout"] = timeout
        return FakeResponse([{"id": "customfield_10016", "name": "Story Points"}])

    monkeypatch.setattr(requests, "get", fake_get)

    client = JiraClient(make_settings())
    fields = client.list_fields()

    assert fields == [{"id": "customfield_10016", "name": "Story Points"}]
    assert captured["url"].endswith("/rest/api/3/field")
    assert captured["timeout"] == 30
