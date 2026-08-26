from __future__ import annotations

import logging

import requests
from requests.auth import HTTPBasicAuth

from ..config import JiraSettings

logger = logging.getLogger(__name__)

_SEARCH_FIELDS = [
    "status",
    "statuscategorychangedate",
    "assignee",
    "parent",
    "issuetype",
    "created",
    "summary",
    "labels",
    "fixVersions",
    "priority",
]

_REQUEST_TIMEOUT_SECONDS = 30


class JiraClient:
    def __init__(self, settings: JiraSettings):
        self._settings = settings
        self._auth = HTTPBasicAuth(username=settings.user, password=settings.token)

    def search_issues(self, jql: str) -> list[dict]:
        fields = [*_SEARCH_FIELDS, self._settings.field_story_points, self._settings.field_sprint]
        url = f"{self._settings.base_url}/rest/api/3/search/jql"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        issues: list[dict] = []
        next_page_token: str | None = None

        while True:
            payload = {
                "expand": "changelog,names",
                "fields": fields,
                "jql": jql,
                "maxResults": self._settings.page_size,
            }
            if next_page_token:
                payload["nextPageToken"] = next_page_token

            logger.debug("Fetching Jira issues with JQL: %s", jql)
            response = requests.post(
                url=url,
                headers=headers,
                json=payload,
                auth=self._auth,
                timeout=_REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()

            issues.extend(data.get("issues", []))

            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break

        return issues

    def list_fields(self) -> list[dict]:
        url = f"{self._settings.base_url}/rest/api/3/field"
        response = requests.get(
            url=url,
            headers={"Accept": "application/json"},
            auth=self._auth,
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()
