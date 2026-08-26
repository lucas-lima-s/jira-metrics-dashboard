from logging.config import fileConfig

from alembic import context

from jira_metrics.config import DatabaseSettings
from jira_metrics.db.engine import sync_db
from jira_metrics.db.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

sync_db.init(DatabaseSettings.from_env())


def run_migrations_online() -> None:
    with sync_db.engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
