import logging
from logging.config import fileConfig

from flask import current_app

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")


def get_engine():
    """
    Retrieve the SQLAlchemy Engine used by Flask-Migrate.
    
    Returns:
        engine: The SQLAlchemy Engine instance used by the Flask application's migration extension. Supports engines exposed via either `db.get_engine()` (Flask-SQLAlchemy < 3 / Alchemical) or `db.engine` (Flask-SQLAlchemy >= 3).
    """
    try:
        # this works with Flask-SQLAlchemy<3 and Alchemical
        return current_app.extensions["migrate"].db.get_engine()
    except (TypeError, AttributeError):
        # this works with Flask-SQLAlchemy>=3
        return current_app.extensions["migrate"].db.engine


def get_engine_url():
    """
    Retrieve the database URL for the current Flask-Migrate engine with percent signs escaped.
    
    Returns:
        db_url (str): The engine's database URL including any password, with '%' characters escaped as '%%'.
    """
    try:
        return get_engine().url.render_as_string(hide_password=False).replace("%", "%%")
    except AttributeError:
        return str(get_engine().url).replace("%", "%%")


# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
config.set_main_option("sqlalchemy.url", get_engine_url())
target_db = current_app.extensions["migrate"].db

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_metadata():
    """
    Return the MetaData object to use as Alembic's target metadata for autogeneration.
    
    When the Flask-Migrate `db` exposes multiple metadatas, selects the default metadata mapped to `None`; otherwise returns the `db.metadata` attribute.
    
    Returns:
        sqlalchemy.MetaData: The MetaData instance used for autogenerate and migration operations.
    """
    if hasattr(target_db, "metadatas"):
        return target_db.metadatas[None]
    return target_db.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=get_metadata(), literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """
    Configure Alembic to run migrations against a live database connection and execute them within a transaction.
    
    Configures a connectable engine and binds a connection to the Alembic context using the module's target metadata and Flask-Migrate configuration. If autogeneration is enabled, registers a directive that suppresses creating an empty revision and logs when no schema changes are detected. Runs migrations inside a transactional context.
    """

    # this callback is used to prevent an auto-migration from being generated
    # when there are no changes to the schema
    # reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
    def process_revision_directives(context, revision, directives):
        """
        Suppress generation of an empty autogenerate migration and log when no schema changes are detected.
        
        If Alembic's autogenerate option is enabled and the computed upgrade operations are empty, this function clears the `directives` list (preventing a new empty revision from being produced) and logs an informational message.
        
        Parameters:
            context: The Alembic MigrationContext for the current run.
            revision: The current revision identifier or directive object provided by Alembic.
            directives (list): The list of pending revision directives; this function may modify this list in-place.
        """
        if getattr(config.cmd_opts, "autogenerate", False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info("No changes in schema detected.")

    conf_args = current_app.extensions["migrate"].configure_args
    if conf_args.get("process_revision_directives") is None:
        conf_args["process_revision_directives"] = process_revision_directives

    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=get_metadata(), **conf_args
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()