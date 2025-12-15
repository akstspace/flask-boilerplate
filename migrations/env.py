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
    Obtain the SQLAlchemy Engine used by the Flask application's migrate extension.
    
    Returns:
        engine: The SQLAlchemy Engine instance used by Flask-Migrate/Flask-SQLAlchemy.
    """
    try:
        # this works with Flask-SQLAlchemy<3 and Alchemical
        return current_app.extensions["migrate"].db.get_engine()
    except (TypeError, AttributeError):
        # this works with Flask-SQLAlchemy>=3
        return current_app.extensions["migrate"].db.engine


def get_engine_url():
    """
    Get the database connection URL string for Alembic with passwords retained and percent signs escaped.
    
    Returns:
        str: The engine URL with the password included and any '%' characters replaced with '%%'.
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
    Return the SQLAlchemy MetaData object used as the autogeneration target.
    
    Prefers the SQLAlchemy 2.0-style metadatas mapping (the entry at key `None`) when present; otherwise falls back to the legacy `metadata` attribute.
    
    Returns:
        sqlalchemy.MetaData: MetaData instance representing the application's models/schema.
    """
    if hasattr(target_db, "metadatas"):
        return target_db.metadatas[None]
    return target_db.metadata


def run_migrations_offline():
    """
    Run Alembic migrations using the configured SQLAlchemy URL without creating a live Engine connection.
    
    Configures the Alembic context with the `sqlalchemy.url` main option and the module's target metadata, enables literal binds for SQL rendering, and executes migrations within a transactional block.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=get_metadata(), literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """
    Run Alembic migrations against the application's database using a live DB connection.
    
    Configures the Alembic context with the application's engine, target metadata, and configured arguments, then executes migrations inside a transactional connection. When autogeneration is requested, suppresses creating an empty migration and logs "No changes in schema detected." if no schema changes are found.
    """

    # this callback is used to prevent an auto-migration from being generated
    # when there are no changes to the schema
    # reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
    def process_revision_directives(context, revision, directives):
        """
        Suppresses creation of an empty autogenerate migration revision.
        
        If autogeneration was requested and the first directive's upgrade operations are empty, clears the
        directives list to prevent generating an empty revision and logs an informational message.
        
        Parameters:
            context: The Alembic migration context provided to the hook.
            revision: The current revision identifier or revision context passed by Alembic.
            directives: A list of revision directives; this function may modify it (clears it) to skip
                creating a migration when there are no schema changes.
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