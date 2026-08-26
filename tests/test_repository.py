from contextlib import contextmanager

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from jira_metrics.db.models import Base, JiraIssue
from jira_metrics.db.repository import (
    insert_or_update_issues,
    purge_demo_data,
    upsert_issues,
    wait_for_database,
)
from jira_metrics.jira.mapping import IssueDTO


def make_issue(key: str, status: str = "TO DO", **overrides) -> IssueDTO:
    defaults = dict(
        issue_key=key,
        status=status,
        resolved=None,
        assignee=None,
        parent=None,
        started=None,
        story_points=0,
        issue_type="Story",
        created=None,
        summary="summary",
        sprint_name=None,
        release=None,
        priority_id=None,
        priority_name=None,
        has_team_label=False,
    )
    defaults.update(overrides)
    return IssueDTO(**defaults)


@pytest.fixture
def session_factory():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    @contextmanager
    def get_session():
        session = factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    return get_session


def _all_issues(session_factory) -> list[JiraIssue]:
    with session_factory() as session:
        return list(session.execute(select(JiraIssue)).scalars().all())


def test_insert_then_update_keeps_one_row(session_factory):
    upsert_issues(session_factory, [make_issue("DEMO-1", summary="first")])
    upsert_issues(session_factory, [make_issue("DEMO-1", summary="second")])

    rows = _all_issues(session_factory)
    assert len(rows) == 1
    assert rows[0].summary == "second"


def test_stale_non_done_row_is_deleted(session_factory):
    upsert_issues(session_factory, [make_issue("DEMO-1", status="TO DO")])
    upsert_issues(session_factory, [make_issue("DEMO-2", status="TO DO")])

    keys = {row.issue_key for row in _all_issues(session_factory)}
    assert keys == {"DEMO-2"}


def test_stale_done_row_is_kept(session_factory):
    upsert_issues(session_factory, [make_issue("DEMO-1", status="DONE")])
    upsert_issues(session_factory, [make_issue("DEMO-2", status="TO DO")])

    keys = {row.issue_key for row in _all_issues(session_factory)}
    assert keys == {"DEMO-1", "DEMO-2"}


def test_insert_or_update_never_deletes_other_rows(session_factory):
    upsert_issues(session_factory, [make_issue("REAL-1", status="TO DO")])
    insert_or_update_issues(session_factory, [make_issue("DEMO-1", status="TO DO")])

    keys = {row.issue_key for row in _all_issues(session_factory)}
    assert keys == {"REAL-1", "DEMO-1"}


def test_wait_for_database_returns_once_connection_succeeds(session_factory):
    wait_for_database(session_factory, retries=1, delay=0)


def test_wait_for_database_raises_after_exhausting_retries():
    def broken_session_factory():
        raise RuntimeError("no database here")

    with pytest.raises(RuntimeError, match="Could not connect"):
        wait_for_database(broken_session_factory, retries=2, delay=0)


def test_purge_demo_data_only_removes_demo_rows(session_factory):
    upsert_issues(session_factory, [make_issue("REAL-1"), make_issue("DEMO-1")])

    removed = purge_demo_data(session_factory)

    assert removed == 1
    keys = {row.issue_key for row in _all_issues(session_factory)}
    assert keys == {"REAL-1"}
