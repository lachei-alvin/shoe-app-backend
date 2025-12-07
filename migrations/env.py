from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from models import Base  # Make sure this imports all your models

# Alembic Config object
config = context.config

# Set up Python logging from the config file
fileConfig(config.config_file_name)

# Provide metadata for 'autogenerate' support
target_metadata = Base.metadata


# Offline migration mode
def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# Online migration mode
def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# Run migrations depending on mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
