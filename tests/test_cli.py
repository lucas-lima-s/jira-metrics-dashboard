import jira_metrics.cli as cli


def _clear_jira_env(monkeypatch):
    for var in ["JIRA_BASE_URL", "JIRA_USER", "JIRA_TOKEN", "JIRA_PROJECT"]:
        monkeypatch.delenv(var, raising=False)


def test_main_exits_2_on_config_error(monkeypatch, capsys):
    _clear_jira_env(monkeypatch)
    monkeypatch.setattr(cli, "_init_db", lambda: None)

    exit_code = cli.main(["collect", "--once"])

    assert exit_code == 2
    assert "error:" in capsys.readouterr().err


def test_build_parser_defaults():
    parser = cli.build_parser()

    collect_args = parser.parse_args(["collect"])
    assert collect_args.once is False
    assert collect_args.func is cli._cmd_collect

    seed_args = parser.parse_args(["seed"])
    assert seed_args.reset is False
    assert seed_args.purge is False
    assert seed_args.issues == cli.DEFAULT_ISSUES_PER_SPRINT
    assert seed_args.sprints == cli.DEFAULT_SPRINTS
    assert seed_args.func is cli._cmd_seed

    migrate_args = parser.parse_args(["migrate"])
    assert migrate_args.func is cli._cmd_migrate

    fields_args = parser.parse_args(["fields", "--contains", "story"])
    assert fields_args.contains == "story"
    assert fields_args.func is cli._cmd_fields


def test_cmd_collect_once_calls_collect_once(monkeypatch, capsys):
    monkeypatch.setattr(cli, "_init_db", lambda: None)
    monkeypatch.setattr(cli, "wait_for_database", lambda *_a, **_k: None)
    monkeypatch.setattr(cli.JiraSettings, "from_env", classmethod(lambda cls, env=None: object()))
    monkeypatch.setattr(cli, "collect_once", lambda *_a, **_k: 7)

    exit_code = cli.main(["collect", "--once"])

    assert exit_code == 0
    assert "Collected 7 issues" in capsys.readouterr().out


def test_cmd_collect_forever_calls_run_forever(monkeypatch):
    monkeypatch.setattr(cli, "_init_db", lambda: None)
    monkeypatch.setattr(cli, "wait_for_database", lambda *_a, **_k: None)
    monkeypatch.setattr(cli.JiraSettings, "from_env", classmethod(lambda cls, env=None: object()))
    called = {}
    monkeypatch.setattr(cli, "run_forever", lambda *a, **k: called.setdefault("args", a))

    exit_code = cli.main(["collect"])

    assert exit_code == 0
    assert called["args"]


def test_cmd_seed_purge(monkeypatch, capsys):
    monkeypatch.setattr(cli, "_init_db", lambda: None)
    monkeypatch.setattr(cli, "wait_for_database", lambda *_a, **_k: None)
    monkeypatch.setattr(cli, "purge_demo_data", lambda *_a, **_k: 3)

    exit_code = cli.main(["seed", "--purge"])

    assert exit_code == 0
    assert "Removed 3 demo rows" in capsys.readouterr().out


def test_cmd_seed_reset(monkeypatch, capsys):
    monkeypatch.setattr(cli, "_init_db", lambda: None)
    monkeypatch.setattr(cli, "wait_for_database", lambda *_a, **_k: None)
    monkeypatch.setattr(cli, "seed_demo_data", lambda *_a, **_k: 240)

    exit_code = cli.main(["seed", "--reset"])

    assert exit_code == 0
    assert "Seeded 240 demo issues" in capsys.readouterr().out


def test_cmd_migrate_invokes_alembic_upgrade(monkeypatch):
    calls = {}

    def fake_upgrade(config, revision):
        calls["revision"] = revision

    monkeypatch.setattr("alembic.command.upgrade", fake_upgrade)

    exit_code = cli.main(["migrate"])

    assert exit_code == 0
    assert calls["revision"] == "head"


def test_cmd_fields_filters_by_contains(monkeypatch, capsys):
    class FakeClient:
        def __init__(self, _settings):
            pass

        def list_fields(self):
            return [
                {"id": "customfield_10016", "name": "Story Points"},
                {"id": "customfield_10020", "name": "Sprint"},
            ]

    monkeypatch.setattr(cli.JiraSettings, "from_env", classmethod(lambda cls, env=None: object()))
    monkeypatch.setattr(cli, "JiraClient", FakeClient)

    exit_code = cli.main(["fields", "--contains", "story"])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "customfield_10016" in out
    assert "customfield_10020" not in out
