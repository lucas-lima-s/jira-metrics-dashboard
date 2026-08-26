from __future__ import annotations

import logging
import time
from collections.abc import Callable
from contextlib import AbstractContextManager

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from ..jira.mapping import IssueDTO
from .models import JiraIssue

logger = logging.getLogger(__name__)

SessionFactory = Callable[[], AbstractContextManager[Session]]

DONE_STATUS = "DONE"


def wait_for_database(session_factory: SessionFactory, retries: int = 10, delay: int = 5) -> None:
    logger.info("Waiting for the database to accept connections...")
    for attempt in range(1, retries + 1):
        try:
            with session_factory() as session:
                if session.execute(text("SELECT 1")).scalar() == 1:
                    logger.info("Database connection established.")
                    return
        except Exception as exc:
            logger.warning("Attempt %d/%d - waiting for database: %s", attempt, retries, exc)
            time.sleep(delay)

    raise RuntimeError("Could not connect to the database")


def _merge_issues(session: Session, issues: list[IssueDTO]) -> None:
    issue_keys = [issue.issue_key for issue in issues]

    existing_ids = dict(
        session.execute(
            select(JiraIssue.issue_key, JiraIssue.id).where(JiraIssue.issue_key.in_(issue_keys))
        ).all()
    )

    for issue in issues:
        data = issue.model_dump()
        data["id"] = existing_ids.get(data["issue_key"])
        session.merge(JiraIssue(**data))


def upsert_issues(session_factory: SessionFactory, issues: list[IssueDTO]) -> int:
    """Full sync: insert/update every issue in `issues` and drop stale open
    issues that are no longer part of the batch. Meant for the live collector,
    which fetches the project's complete current issue set on every run."""
    with session_factory() as session:
        issue_keys = [issue.issue_key for issue in issues]

        session.execute(
            delete(JiraIssue).where(
                JiraIssue.issue_key.notin_(issue_keys),
                JiraIssue.status != DONE_STATUS,
            )
        )

        _merge_issues(session, issues)

        return len(issues)


def insert_or_update_issues(session_factory: SessionFactory, issues: list[IssueDTO]) -> int:
    """Insert/update the given issues without touching any other row. Used by
    the demo seeder so it never deletes real, independently-collected data."""
    with session_factory() as session:
        _merge_issues(session, issues)
        return len(issues)


def purge_demo_data(session_factory: SessionFactory) -> int:
    with session_factory() as session:
        result = session.execute(delete(JiraIssue).where(JiraIssue.issue_key.like("DEMO-%")))
        return result.rowcount or 0
