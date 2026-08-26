from contextlib import contextmanager

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from jira_metrics.db.models import Base, JiraIssue
from jira_metrics.demo_seed import build_demo_issues, seed_demo_data

REAL_SURNAMES = ["NOGUEIRA", "AQUINO", "NASCIMENTO", "RIBEIRO", "NOVAIS"]


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


def test_deterministic_across_calls():
    first = build_demo_issues(seed=42)
    second = build_demo_issues(seed=42)
    assert first == second


def test_length_matches_sprints_times_issues_per_sprint():
    issues = build_demo_issues(seed=42, sprints=6, issues_per_sprint=40)
    assert len(issues) == 240


def test_keys_are_unique_and_demo_prefixed():
    issues = build_demo_issues(seed=42)
    keys = [issue.issue_key for issue in issues]
    assert len(keys) == len(set(keys))
    assert all(key.startswith("DEMO-") for key in keys)


def test_mismatch_scenarios_exist_in_both_directions():
    issues = build_demo_issues(seed=42)

    demo_board_false = [
        i for i in issues if i.sprint_name.startswith("Demo Board") and i.has_team_label is False
    ]
    other_board_true = [
        i for i in issues if not i.sprint_name.startswith("Demo Board") and i.has_team_label is True
    ]

    assert len(demo_board_false) >= 1
    assert len(other_board_true) >= 1


def test_no_assignee_matches_real_ex_colleague_names():
    issues = build_demo_issues(seed=42)
    assignees = {i.assignee for i in issues if i.assignee}
    for assignee in assignees:
        for surname in REAL_SURNAMES:
            assert surname not in assignee


def test_seed_demo_data_writes_rows(session_factory):
    count = seed_demo_data(session_factory, sprints=2, issues_per_sprint=5)

    assert count == 10
    with session_factory() as session:
        rows = session.execute(select(JiraIssue)).scalars().all()
    assert len(rows) == 10


def test_seed_demo_data_reset_only_touches_demo_rows(session_factory):
    from jira_metrics.db.repository import upsert_issues
    from jira_metrics.jira.mapping import IssueDTO

    real_issue = IssueDTO(
        issue_key="REAL-1",
        status="TO DO",
        resolved=None,
        assignee=None,
        parent=None,
        started=None,
        story_points=0,
        issue_type="Story",
        created=None,
        summary="real work",
        sprint_name=None,
        release=None,
        priority_id=None,
        priority_name=None,
        has_team_label=False,
    )
    upsert_issues(session_factory, [real_issue])

    seed_demo_data(session_factory, reset=True, sprints=1, issues_per_sprint=3)

    with session_factory() as session:
        keys = {row.issue_key for row in session.execute(select(JiraIssue)).scalars().all()}
    assert "REAL-1" in keys
    assert sum(1 for k in keys if k.startswith("DEMO-")) == 3
