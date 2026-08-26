from contextlib import contextmanager

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from jira_metrics.config import JiraSettings
from jira_metrics.db.models import Base, JiraIssue
from jira_metrics.service import collect_once, run_forever


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


class FakeClient:
    def __init__(self, raw_issues):
        self._raw_issues = raw_issues
        self.calls = 0

    def search_issues(self, jql):
        self.calls += 1
        return self._raw_issues


def test_collect_once_persists_mapped_issues(session_factory):
    raw_issues = [
        {"key": "DEMO-1", "fields": {"status": {"name": "To Do"}, "summary": "one"}},
        {"key": "DEMO-2", "fields": {"status": {"name": "Done"}, "summary": "two"}},
    ]
    client = FakeClient(raw_issues)

    count = collect_once(session_factory, make_settings(), client=client)

    assert count == 2
    assert client.calls == 1
    with session_factory() as session:
        keys = {row.issue_key for row in session.execute(select(JiraIssue)).scalars().all()}
    assert keys == {"DEMO-1", "DEMO-2"}


def test_run_forever_stops_after_sleep_raises(session_factory, monkeypatch):
    client = FakeClient([])
    calls = {"sleep": 0}

    def fake_sleep(_seconds):
        calls["sleep"] += 1
        raise KeyboardInterrupt

    monkeypatch.setattr("jira_metrics.service.time.sleep", fake_sleep)

    with pytest.raises(KeyboardInterrupt):
        run_forever(session_factory, make_settings(), fetch_interval_seconds=0, client=client)

    assert calls["sleep"] == 1


def test_run_forever_logs_and_continues_on_error(session_factory, monkeypatch):
    class BrokenClient:
        def search_issues(self, jql):
            raise RuntimeError("jira is down")

    call_count = {"n": 0}

    def fake_sleep(_seconds):
        call_count["n"] += 1
        if call_count["n"] >= 1:
            raise KeyboardInterrupt

    monkeypatch.setattr("jira_metrics.service.time.sleep", fake_sleep)

    with pytest.raises(KeyboardInterrupt):
        run_forever(
            session_factory, make_settings(), fetch_interval_seconds=0, client=BrokenClient()
        )
