from __future__ import annotations

import logging
import time

from .config import JiraSettings
from .db.repository import SessionFactory, upsert_issues
from .jira.client import JiraClient
from .jira.jql import build_jql
from .jira.mapping import issue_to_dto

logger = logging.getLogger(__name__)


def collect_once(
    session_factory: SessionFactory, jira_settings: JiraSettings, client: JiraClient | None = None
) -> int:
    client = client or JiraClient(jira_settings)
    jql = build_jql(jira_settings.project, jira_settings.labels)

    logger.debug("Fetching issues with JQL: %s", jql)
    raw_issues = client.search_issues(jql)
    logger.info("Fetched %d issues from Jira", len(raw_issues))

    issues = [issue_to_dto(issue, jira_settings) for issue in raw_issues]
    upsert_issues(session_factory, issues)

    return len(issues)


def run_forever(
    session_factory: SessionFactory,
    jira_settings: JiraSettings,
    fetch_interval_seconds: int,
    client: JiraClient | None = None,
) -> None:
    while True:
        try:
            count = collect_once(session_factory, jira_settings, client=client)
            logger.info("Collected %d issues", count)
        except Exception:
            logger.exception("Error while collecting issues")

        time.sleep(fetch_interval_seconds)
