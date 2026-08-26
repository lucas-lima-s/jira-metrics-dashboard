import json
import re
from pathlib import Path

DASHBOARD_PATH = (
    Path(__file__).parent.parent
    / "grafana"
    / "provisioning"
    / "dashboards"
    / "jira-delivery-metrics.json"
)

FORBIDDEN_PATTERN = re.compile(
    r"e-?[dD]eploy|edeploy\.atlassian|iFood|IFOOD|\bRBI\b|systools|\bAPED\b|\bOXAP\b"
    r"|POS ?- ?TS|POS-WTC|Sacola|ATATT[0-9A-Za-z]|customfield_10041|customfield_10008"
    r"|drythz|C:[\\/]Users|D:[\\/]Projects|OneDrive|ALBERT DAVID|ANDRESSA|CLAUDINEI"
    r"|JOAO\.RIBEIRO|PEDRO HENRIQUE|lucas\.lima@"
)


def _raw_text() -> str:
    return DASHBOARD_PATH.read_text(encoding="utf-8")


def _dashboard() -> dict:
    return json.loads(_raw_text())


def _all_raw_sql(dashboard: dict) -> list[str]:
    sqls = []

    def walk(panels):
        for panel in panels:
            for target in panel.get("targets", []):
                if "rawSql" in target:
                    sqls.append(target["rawSql"])
            if panel.get("panels"):
                walk(panel["panels"])

    walk(dashboard["panels"])
    return sqls


def test_dashboard_file_is_valid_json():
    _dashboard()


def test_dashboard_uid_is_stable():
    assert _dashboard()["uid"] == "jira-delivery-metrics"


def test_every_panel_datasource_uid_is_the_provisioned_one():
    dashboard = _dashboard()

    def walk(panels):
        for panel in panels:
            ds = panel.get("datasource")
            if ds:
                assert ds["uid"] == "jira-metrics-postgres"
            for target in panel.get("targets", []):
                target_ds = target.get("datasource")
                if target_ds:
                    assert target_ds["uid"] == "jira-metrics-postgres"
            if panel.get("panels"):
                walk(panel["panels"])

    walk(dashboard["panels"])


def test_no_forbidden_tokens_in_dashboard():
    assert FORBIDDEN_PATTERN.search(_raw_text()) is None


def test_mismatch_panel_uses_or_not_and():
    dashboard = _dashboard()
    sqls = _all_raw_sql(dashboard)
    mismatch_sql = next(sql for sql in sqls if "OR (has_team_label IS TRUE" in sql)

    assert "OR (has_team_label IS TRUE" in mismatch_sql
    assert "IS FALSE)\r\n  AND (" not in mismatch_sql
    assert "IS FALSE)\n  AND (" not in mismatch_sql


def test_no_raw_sql_references_removed_employer_filter():
    dashboard = _dashboard()
    for sql in _all_raw_sql(dashboard):
        assert "Sacola" not in sql
        assert "POS - TS" not in sql


def test_every_average_history_division_is_null_safe():
    dashboard = _dashboard()
    for sql in _all_raw_sql(dashboard):
        for match in re.finditer(r"/\s*(NULLIF\(average_history, 0\)|average_history)", sql):
            assert match.group(1).startswith("NULLIF"), sql
