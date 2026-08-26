from __future__ import annotations

import logging
import random
from datetime import UTC, datetime, timedelta

from .db.repository import SessionFactory, insert_or_update_issues, purge_demo_data
from .jira.mapping import IssueDTO

logger = logging.getLogger(__name__)

DEVS = ["ANA.SOUZA", "BRUNO.ALVES", "CARLA.MENDES", "DIEGO.ROCHA", "ELENA.DIAS"]
UNASSIGNED_RATE = 0.08
MISMATCH_RATE = 0.08
OTHER_BOARD_ISSUES = 6

ISSUE_TYPE_WEIGHTS = [("Story", 55), ("Bug", 30), ("Task", 10), ("Epic", 5)]
STORY_POINTS = [1, 2, 3, 5, 8, 13]
PRIORITIES = [("1", "Highest"), ("2", "High"), ("3", "Medium"), ("4", "Low")]

SPRINT_LENGTH_DAYS = 14
SPRINTS_PER_RELEASE = 3
RELEASES = ["26.01", "26.02"]


def _weighted_choice(rng: random.Random, weights: list[tuple[str, int]]) -> str:
    total = sum(weight for _, weight in weights)
    pick = rng.uniform(0, total)
    upto = 0.0
    for value, weight in weights:
        upto += weight
        if pick <= upto:
            return value
    return weights[-1][0]


def _sprint_plan(sprints: int, anchor_end: datetime) -> list[dict]:
    plan = []
    for index in range(sprints):
        release_index, sprint_in_release = divmod(index, SPRINTS_PER_RELEASE)
        release = RELEASES[release_index % len(RELEASES)]
        sprint_number = sprint_in_release + 1
        offset_sprints_from_last = sprints - index - 1
        end = anchor_end - timedelta(days=SPRINT_LENGTH_DAYS * offset_sprints_from_last)
        start = end - timedelta(days=SPRINT_LENGTH_DAYS)
        plan.append(
            {
                "name": f"Demo Board - {release} - SP{sprint_number:02d}",
                "release": f"Demo Release {release}",
                "start": start,
                "end": end,
                "is_current": index == sprints - 1,
            }
        )
    return plan


def _assignee(rng: random.Random) -> str | None:
    if rng.random() < UNASSIGNED_RATE:
        return None
    return rng.choice(DEVS)


def _status_for(rng: random.Random, is_current: bool) -> str:
    if not is_current:
        return "DONE"
    return rng.choices(["TO DO", "IN PROGRESS", "DONE"], weights=[35, 30, 35])[0]


def build_demo_issues(
    seed: int = 42, sprints: int = 6, issues_per_sprint: int = 40
) -> list[IssueDTO]:
    rng = random.Random(seed)
    anchor_end = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    plan = _sprint_plan(sprints, anchor_end)

    issues: list[IssueDTO] = []
    counter = 0

    for sprint in plan:
        for _ in range(issues_per_sprint):
            counter += 1
            issue_type = _weighted_choice(rng, ISSUE_TYPE_WEIGHTS)
            status = _status_for(rng, sprint["is_current"])
            created = sprint["start"] + timedelta(hours=rng.uniform(0, 24))
            started = created + timedelta(hours=rng.uniform(1, 48)) if status != "TO DO" else None
            resolved = (
                sprint["end"] - timedelta(hours=rng.uniform(0, 12)) if status == "DONE" else None
            )
            priority_id, priority_name = rng.choice(PRIORITIES)
            has_team_label = rng.random() >= MISMATCH_RATE

            issues.append(
                IssueDTO(
                    issue_key=f"DEMO-{counter}",
                    status=status,
                    resolved=resolved,
                    assignee=_assignee(rng),
                    parent=None,
                    started=started,
                    story_points=rng.choice(STORY_POINTS),
                    issue_type=issue_type,
                    created=created,
                    summary=f"{issue_type} #{counter} in {sprint['name']}",
                    sprint_name=sprint["name"],
                    release=sprint["release"],
                    priority_id=priority_id,
                    priority_name=priority_name,
                    has_team_label=has_team_label,
                )
            )

    other_board_end = anchor_end
    other_board_start = other_board_end - timedelta(days=SPRINT_LENGTH_DAYS)
    for offset in range(1, min(OTHER_BOARD_ISSUES, len(issues)) + 1):
        target_index = -offset
        original = issues[target_index]
        created = other_board_start + timedelta(hours=rng.uniform(0, 24))
        issues[target_index] = original.model_copy(
            update={
                "sprint_name": "Other Board - Misc",
                "release": None,
                "has_team_label": True,
                "created": created,
            }
        )

    return issues


def seed_demo_data(session_factory: SessionFactory, reset: bool = False, **kwargs) -> int:
    if reset:
        removed = purge_demo_data(session_factory)
        logger.info("Removed %d existing demo rows", removed)

    issues = build_demo_issues(**kwargs)
    insert_or_update_issues(session_factory, issues)
    logger.info("Seeded %d demo issues", len(issues))
    return len(issues)
