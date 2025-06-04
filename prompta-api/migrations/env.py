from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Import your app's database configuration and models
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.config import settings

# Import all your models - this ensures they're registered with Base
from models import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override the sqlalchemy.url with your app's database URL
config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# Define table creation order to handle circular dependencies
TABLE_ORDER = [
    "users",  # No dependencies
    "projects",  # Depends on users
    "api_keys",  # Depends on users
    "prompts",  # Depends on users and projects (without current_version_id FK)
    "prompt_versions",  # Depends on prompts
]


def include_object(object, name, type_, reflected, compare_to):
    """Custom include_object hook to handle table ordering and circular dependencies."""
    return True


def process_revision_directives(context, revision, directives):
    """Custom hook to reorder table operations to handle dependencies."""
    if getattr(context.config.cmd_opts, "autogenerate", False):
        script = directives[0]
        if script.upgrade_ops:
            # Separate create_table and other operations
            create_ops = []
            other_ops = []

            for op in script.upgrade_ops.ops:
                if (
                    hasattr(op, "table_name")
                    and op.__class__.__name__ == "CreateTableOp"
                ):
                    create_ops.append(op)
                else:
                    other_ops.append(op)

            # Sort create_table operations by our defined order
            def get_table_order(op):
                table_name = getattr(op, "table_name", "")
                try:
                    return TABLE_ORDER.index(table_name)
                except ValueError:
                    return 999  # Put unknown tables at the end

            create_ops.sort(key=get_table_order)

            # Rebuild operations list with proper order
            script.upgrade_ops.ops = create_ops + other_ops


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        process_revision_directives=process_revision_directives,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            process_revision_directives=process_revision_directives,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
