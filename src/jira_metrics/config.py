from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass


class ConfigError(RuntimeError):
    pass


def _split_labels(raw: str) -> tuple[str, ...]:
    return tuple(sorted({label.strip() for label in raw.split(",") if label.strip()}))


def _as_bool(raw: str) -> bool:
    return raw.strip().lower() == "true"


@dataclass(frozen=True)
class JiraSettings:
    base_url: str
    user: str
    token: str
    project: str
    labels: tuple[str, ...]
    team_label: str | None
    field_story_points: str
    field_sprint: str
    page_size: int

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> JiraSettings:
        env = env if env is not None else os.environ

        required = {
            "JIRA_BASE_URL": env.get("JIRA_BASE_URL"),
            "JIRA_USER": env.get("JIRA_USER"),
            "JIRA_TOKEN": env.get("JIRA_TOKEN"),
            "JIRA_PROJECT": env.get("JIRA_PROJECT"),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ConfigError("missing required environment variables: " + ", ".join(missing))

        team_label = env.get("JIRA_TEAM_LABEL", "").strip() or None

        return cls(
            base_url=required["JIRA_BASE_URL"].rstrip("/"),
            user=required["JIRA_USER"],
            token=required["JIRA_TOKEN"],
            project=required["JIRA_PROJECT"],
            labels=_split_labels(env.get("JIRA_LABELS", "")),
            team_label=team_label,
            field_story_points=env.get("JIRA_FIELD_STORY_POINTS", "customfield_10016"),
            field_sprint=env.get("JIRA_FIELD_SPRINT", "customfield_10020"),
            page_size=int(env.get("JIRA_PAGE_SIZE", "100")),
        )


@dataclass(frozen=True)
class DatabaseSettings:
    uri: str
    user: str
    password: str
    host: str
    port: str
    name: str
    echo: bool
    pool_size: int
    max_overflow: int
    pool_pre_ping: bool

    @property
    def sqlalchemy_url(self) -> str:
        return f"{self.uri}://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> DatabaseSettings:
        env = env if env is not None else os.environ
        return cls(
            uri=env.get("DATABASE_URI", "postgresql+psycopg"),
            user=env.get("DATABASE_USER", "postgres"),
            password=env.get("DATABASE_PASSWORD", "postgres"),
            host=env.get("DATABASE_HOST", "postgres"),
            port=env.get("DATABASE_PORT", "5432"),
            name=env.get("DATABASE_NAME", "metrics"),
            echo=_as_bool(env.get("SQLALCHEMY_ECHO", "false")),
            pool_size=int(env.get("SQLALCHEMY_POOL_SIZE", "20")),
            max_overflow=int(env.get("SQLALCHEMY_MAX_OVERFLOW", "10")),
            pool_pre_ping=_as_bool(env.get("SQLALCHEMY_POOL_PRE_PING", "true")),
        )


@dataclass(frozen=True)
class RuntimeSettings:
    fetch_interval_seconds: int
    log_level: str

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> RuntimeSettings:
        env = env if env is not None else os.environ
        return cls(
            fetch_interval_seconds=int(env.get("FETCH_INTERVAL_SECONDS", "600")),
            log_level=env.get("LOG_LEVEL", "INFO"),
        )
