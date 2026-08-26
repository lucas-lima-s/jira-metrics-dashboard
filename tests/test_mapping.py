from datetime import datetime

import pytest

from jira_metrics.config import JiraSettings
from jira_metrics.jira.mapping import _coerce_points, _has_team_label, _sprint_name, issue_to_dto


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


def test_full_issue_maps_every_field(fixture):
    issue = fixture("issue_full.json")
    dto = issue_to_dto(issue, make_settings(team_label="tier-s"))

    assert dto.issue_key == "DEMO-1"
    assert dto.status == "DONE"
    assert dto.resolved == datetime.fromisoformat("2026-02-10T15:00:00.000-03:00")
    assert dto.assignee == "ANA.SOUZA"
    assert dto.parent == "DEMO-100"
    assert dto.started == datetime.fromisoformat("2026-02-02T10:00:00.000-03:00")
    assert dto.story_points == 5
    assert dto.issue_type == "Story"
    assert dto.created == datetime.fromisoformat("2026-02-01T09:00:00.000-03:00")
    assert dto.summary == "Implement the thing"
    assert dto.sprint_name == "Sprint 34"
    assert dto.release == "A | B"
    assert dto.priority_id == "2"
    assert dto.priority_name == "High"
    assert dto.has_team_label is True


def test_minimal_issue_has_safe_defaults(fixture):
    issue = fixture("issue_minimal.json")
    dto = issue_to_dto(issue, make_settings())

    assert dto.status == ""
    assert dto.priority_id is None
    assert dto.priority_name is None
    assert dto.has_team_label is False
    assert dto.story_points == 0
    assert dto.sprint_name is None


def test_has_team_label_false_when_labels_key_absent():
    assert _has_team_label(None, "tier-s") is False


def test_has_team_label_false_when_labels_null():
    assert _has_team_label(None, "tier-s") is False


def test_has_team_label_true_when_present():
    assert _has_team_label(["tier-s", "x"], "tier-s") is True


def test_has_team_label_does_not_split_comma_string():
    assert _has_team_label(["a", "b"], "a,b") is False


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(None, 0), ("3", 3), (3.7, 3), ({}, 0)],
)
def test_coerce_points(raw, expected):
    assert _coerce_points(raw) == expected


def test_sprint_name_picks_highest_id_regardless_of_order():
    sprints = [{"id": 5, "name": "later"}, {"id": 2, "name": "earlier"}]
    assert _sprint_name(sprints) == "later"


def test_sprint_name_absent_is_none():
    assert _sprint_name(None) is None


def test_custom_field_ids_come_from_settings_not_hardcoded():
    issue = {
        "key": "DEMO-9",
        "fields": {
            "status": {"name": "To Do"},
            "customfield_77777": "8",
            "customfield_88888": [{"id": 1, "name": "Sprint X"}],
        },
    }
    dto = issue_to_dto(
        issue,
        make_settings(field_story_points="customfield_77777", field_sprint="customfield_88888"),
    )
    assert dto.story_points == 8
    assert dto.sprint_name == "Sprint X"
