from jira_metrics.jira.changelog import status_transition_dates


def _history(created: str, field_id: str, to_string: str) -> dict:
    return {"created": created, "items": [{"fieldId": field_id, "toString": to_string}]}


def test_no_changelog_key_returns_empty_dict():
    assert status_transition_dates({}) == {}


def test_null_changelog_returns_empty_dict():
    assert status_transition_dates({"changelog": None}) == {}


def test_to_string_in_progress_maps_to_uppercase_key():
    issue = {
        "changelog": {
            "histories": [_history("2026-01-01T00:00:00Z", "status", "In Progress")],
        }
    }
    assert status_transition_dates(issue) == {"IN PROGRESS": "2026-01-01T00:00:00Z"}


def test_earliest_transition_wins_when_status_repeats():
    issue = {
        "changelog": {
            "histories": [
                _history("2026-01-01T00:00:00Z", "status", "In Progress"),
                _history("2026-01-05T00:00:00Z", "status", "Done"),
                _history("2026-01-10T00:00:00Z", "status", "In Progress"),
            ]
        }
    }
    result = status_transition_dates(issue)
    assert result["IN PROGRESS"] == "2026-01-01T00:00:00Z"
    assert result["DONE"] == "2026-01-05T00:00:00Z"


def test_non_status_fields_are_ignored():
    issue = {
        "changelog": {
            "histories": [_history("2026-01-01T00:00:00Z", "assignee", "Someone")],
        }
    }
    assert status_transition_dates(issue) == {}
