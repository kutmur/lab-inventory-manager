import logging
from logging.config import fileConfig

from flask import current_app

from alembic import context

# Configure logging from alembic.ini file
config = context.config
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')


def get_engine():
    """Get SQLAlchemy engine from Flask app."""
    try:
        return current_app.extensions['migrate'].db.get_engine()
    except TypeError:
        # This allows running migrations without app context 
        # for --autogenerate
        return current_app.extensions['sqlalchemy'].get_engine()


def get_engine_url():
    """Get database URL from Flask configuration."""
    try:
        return current_app.config.get("SQLALCHEMY_DATABASE_URI")
    except AttributeError:
        return None


# Configure sqlalchemy URL
config.set_main_option('sqlalchemy.url', get_engine_url())
target_db = current_app.extensions['migrate'].db


def get_metadata():
    """Get database metadata from current application."""
    if hasattr(target_db, 'metadatas'):
        return target_db.metadatas[None]
    return target_db.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode.
    
    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine
    creation we don't even need a DBAPI to be available.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, 
        target_metadata=get_metadata(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine and associate a
    connection with the context.
    """
    # This callback is used to prevent an auto-migration from being
    # generated when there are no changes to the schema
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes detected in schema.')

    conf_args = current_app.extensions['migrate'].configure_args
    conf_kwargs = {
        'target_metadata': get_metadata(),
        'process_revision_directives': process_revision_directives,
        **conf_args
    }

    engine = get_engine()
    
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            **conf_kwargs
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
