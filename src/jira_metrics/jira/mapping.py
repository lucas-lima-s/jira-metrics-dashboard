from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from ..config import JiraSettings
from .changelog import status_transition_dates


class IssueDTO(BaseModel):
    issue_key: str
    status: str
    resolved: datetime | None
    assignee: str | None
    parent: str | None
    started: datetime | None
    story_points: int = 0
    issue_type: str | None
    created: datetime | None
    summary: str | None
    sprint_name: str | None
    release: str | None
    priority_id: str | None
    priority_name: str | None
    has_team_label: bool | None

    model_config = {"from_attributes": True}


def _has_team_label(labels, team_label: str | None) -> bool:
    if not team_label:
        return False
    return team_label in {str(x) for x in (labels or [])}


def _coerce_points(raw) -> int:
    try:
        return int(float(raw))
    except (TypeError, ValueError):
        return 0


def _sprint_name(raw) -> str | None:
    entries = [e for e in (raw or []) if isinstance(e, dict)]
    if not entries:
        return None
    return sorted(entries, key=lambda e: e.get("id") or 0)[-1].get("name")


def _fix_versions(raw) -> str | None:
    versions = [v.get("name") for v in (raw or []) if isinstance(v, dict) and v.get("name")]
    return " | ".join(versions) if versions else None


def issue_to_dto(issue: dict, settings: JiraSettings) -> IssueDTO:
    issue_key = issue["key"]
    fields = issue.get("fields") or {}

    status_field = fields.get("status") or {}
    status = (status_field.get("name") or "").upper()
    resolved = fields.get("statuscategorychangedate") if status == "DONE" else None

    assignee_field = fields.get("assignee") or {}
    assignee = assignee_field.get("displayName")
    assignee = assignee.upper() if assignee else None

    status_history = status_transition_dates(issue)
    started_at = status_history.get("IN PROGRESS")

    parent_field = fields.get("parent") or {}
    parent = parent_field.get("key")

    priority = fields.get("priority") or {}
    priority_id = priority.get("id")
    priority_name = priority.get("name")

    return IssueDTO(
        issue_key=issue_key,
        status=status,
        resolved=resolved,
        assignee=assignee,
        parent=parent,
        started=started_at,
        story_points=_coerce_points(fields.get(settings.field_story_points)),
        issue_type=(fields.get("issuetype") or {}).get("name"),
        created=fields.get("created"),
        summary=fields.get("summary"),
        sprint_name=_sprint_name(fields.get(settings.field_sprint)),
        release=_fix_versions(fields.get("fixVersions")),
        priority_id=priority_id,
        priority_name=priority_name,
        has_team_label=_has_team_label(fields.get("labels"), settings.team_label),
    )
