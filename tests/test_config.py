import pytest

from jira_metrics.config import ConfigError, DatabaseSettings, JiraSettings, RuntimeSettings


def test_jira_settings_raises_with_all_missing_vars_listed():
    with pytest.raises(ConfigError) as exc_info:
        JiraSettings.from_env({})

    message = str(exc_info.value)
    for var in ["JIRA_BASE_URL", "JIRA_USER", "JIRA_TOKEN", "JIRA_PROJECT"]:
        assert var in message


def test_jira_settings_from_env_happy_path():
    env = {
        "JIRA_BASE_URL": "https://demo.atlassian.net/",
        "JIRA_USER": "user@example.com",
        "JIRA_TOKEN": "secret",
        "JIRA_PROJECT": "DEMO",
        "JIRA_LABELS": "b, a ,a",
        "JIRA_TEAM_LABEL": "tier-s",
    }
    settings = JiraSettings.from_env(env)

    assert settings.base_url == "https://demo.atlassian.net"
    assert settings.labels == ("a", "b")
    assert settings.team_label == "tier-s"
    assert settings.field_story_points == "customfield_10016"
    assert settings.field_sprint == "customfield_10020"


def test_jira_settings_team_label_defaults_to_none():
    env = {
        "JIRA_BASE_URL": "https://demo.atlassian.net",
        "JIRA_USER": "user@example.com",
        "JIRA_TOKEN": "secret",
        "JIRA_PROJECT": "DEMO",
    }
    assert JiraSettings.from_env(env).team_label is None


def test_database_settings_never_raises_and_has_defaults():
    settings = DatabaseSettings.from_env({})
    assert settings.host == "postgres"
    assert settings.name == "metrics"
    assert settings.sqlalchemy_url == "postgresql+psycopg://postgres:postgres@postgres:5432/metrics"


def test_runtime_settings_defaults():
    settings = RuntimeSettings.from_env({})
    assert settings.fetch_interval_seconds == 600
    assert settings.log_level == "INFO"
