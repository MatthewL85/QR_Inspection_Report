import logging
from logging.config import fileConfig

from flask import current_app
from alembic import context

# Alembic Config object
config = context.config

# 🔧 Configure file-based logging from alembic.ini
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# ✅ Import all models (AI/GAR future-proofed, not just temp models)
from app.extensions import db
from app.models import *  # All models imported from __init__.py

# 🎯 Metadata from full project models
target_metadata = db.Model.metadata

def get_engine():
    """Get the SQLAlchemy engine from the current Flask app context."""
    try:
        return current_app.extensions['migrate'].db.get_engine()
    except (TypeError, AttributeError):
        return current_app.extensions['migrate'].db.engine

def get_engine_url():
    """Safely retrieve the database URL for Alembic configuration."""
    try:
        return get_engine().url.render_as_string(hide_password=False).replace('%', '%%')
    except AttributeError:
        return str(get_engine().url).replace('%', '%%')

# ✅ Inject engine URL into Alembic config
config.set_main_option('sqlalchemy.url', get_engine_url())

def run_migrations_offline():
    """Run migrations in 'offline' mode (no DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode (with live DB connection)."""
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('✅ No schema changes detected.')

    conf_args = current_app.extensions['migrate'].configure_args

    # 🛠 Ensure no duplication of compare_type
    conf_args.setdefault("compare_type", True)

    if conf_args.get("process_revision_directives") is None:
        conf_args["process_revision_directives"] = process_revision_directives

    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            **conf_args  # ✅ compare_type already inside
        )
        with context.begin_transaction():
            context.run_migrations()

# 🚀 Choose run mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
