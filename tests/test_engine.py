from dataclasses import dataclass

import pytest
from sqlalchemy import text

from jira_metrics.db.engine import SyncDatabase


@dataclass(frozen=True)
class FakeSettings:
    sqlalchemy_url: str = "sqlite://"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 5
    pool_pre_ping: bool = False


def test_engine_property_raises_before_init():
    db = SyncDatabase()
    with pytest.raises(RuntimeError):
        _ = db.engine


def test_init_and_session_roundtrip():
    db = SyncDatabase()
    db.init(FakeSettings())

    assert db.engine is not None

    with db.get_session() as session:
        assert session.execute(text("SELECT 1")).scalar() == 1

    with db.get_session_with_transaction() as session:
        assert session.execute(text("SELECT 1")).scalar() == 1


def test_session_with_transaction_rolls_back_on_error():
    db = SyncDatabase()
    db.init(FakeSettings())

    with pytest.raises(ValueError), db.get_session_with_transaction() as session:
        session.execute(text("SELECT 1"))
        raise ValueError("boom")
