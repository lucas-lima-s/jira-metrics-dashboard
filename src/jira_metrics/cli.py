from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

load_dotenv()

from .config import ConfigError, DatabaseSettings, JiraSettings, RuntimeSettings  # noqa: E402
from .db.engine import sync_db  # noqa: E402
from .db.repository import purge_demo_data, wait_for_database  # noqa: E402
from .demo_seed import seed_demo_data  # noqa: E402
from .jira.client import JiraClient  # noqa: E402
from .logging_setup import configure_logging  # noqa: E402
from .service import collect_once, run_forever  # noqa: E402

DEFAULT_SEED = 42
DEFAULT_SPRINTS = 6
DEFAULT_ISSUES_PER_SPRINT = 40


def _init_db() -> None:
    sync_db.init(DatabaseSettings.from_env())


def _cmd_collect(args: argparse.Namespace) -> int:
    runtime = RuntimeSettings.from_env()
    configure_logging(runtime.log_level)
    jira_settings = JiraSettings.from_env()
    _init_db()

    wait_for_database(sync_db.get_session_with_transaction)

    if args.once:
        count = collect_once(sync_db.get_session_with_transaction, jira_settings)
        print(f"Collected {count} issues")
    else:
        run_forever(
            sync_db.get_session_with_transaction,
            jira_settings,
            runtime.fetch_interval_seconds,
        )
    return 0


def _cmd_seed(args: argparse.Namespace) -> int:
    configure_logging(RuntimeSettings.from_env().log_level)
    _init_db()

    wait_for_database(sync_db.get_session_with_transaction)

    if args.purge:
        removed = purge_demo_data(sync_db.get_session_with_transaction)
        print(f"Removed {removed} demo rows")
        return 0

    count = seed_demo_data(
        sync_db.get_session_with_transaction,
        reset=args.reset,
        seed=DEFAULT_SEED,
        sprints=args.sprints,
        issues_per_sprint=args.issues,
    )
    print(f"Seeded {count} demo issues")
    return 0


def _cmd_migrate(_args: argparse.Namespace) -> int:
    from alembic import command
    from alembic.config import Config

    configure_logging(RuntimeSettings.from_env().log_level)
    command.upgrade(Config("alembic.ini"), "head")
    return 0


def _cmd_fields(args: argparse.Namespace) -> int:
    configure_logging(RuntimeSettings.from_env().log_level)
    jira_settings = JiraSettings.from_env()
    client = JiraClient(jira_settings)

    for field in client.list_fields():
        name = field.get("name", "")
        if args.contains and args.contains.lower() not in name.lower():
            continue
        print(f"{field.get('id')}  {name}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jira-metrics")
    subparsers = parser.add_subparsers(dest="command", required=True)

    collect_parser = subparsers.add_parser("collect", help="Collect issues from Jira")
    collect_parser.add_argument("--once", action="store_true", help="Run a single collection pass")
    collect_parser.set_defaults(func=_cmd_collect)

    seed_parser = subparsers.add_parser("seed", help="Seed the database with demo data")
    seed_parser.add_argument("--reset", action="store_true", help="Delete existing demo rows first")
    seed_parser.add_argument(
        "--purge", action="store_true", help="Only delete demo rows, do not reseed"
    )
    seed_parser.add_argument(
        "--issues", type=int, default=DEFAULT_ISSUES_PER_SPRINT, help="Issues per sprint"
    )
    seed_parser.add_argument(
        "--sprints", type=int, default=DEFAULT_SPRINTS, help="Number of sprints"
    )
    seed_parser.set_defaults(func=_cmd_seed)

    migrate_parser = subparsers.add_parser("migrate", help="Run database migrations")
    migrate_parser.set_defaults(func=_cmd_migrate)

    fields_parser = subparsers.add_parser("fields", help="List available Jira fields")
    fields_parser.add_argument("--contains", help="Filter fields whose name contains TEXT")
    fields_parser.set_defaults(func=_cmd_fields)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
