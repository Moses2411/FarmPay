# alembic/env.py
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

# Load .env BEFORE importing anything that needs DATABASE_URL
from dotenv import load_dotenv
load_dotenv()

from alembic import context

# Add your project directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import your Base and models
from db.database import Base
import db.model

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate
target_metadata = Base.metadata

def get_url():
    """Get database URL - defaults to SQLite for local dev"""
    url = os.getenv("DATABASE_URL")
    
    # Only use PostgreSQL if explicitly provided and valid
    if url and (url.startswith("postgresql://") or url.startswith("postgres://")):
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
    else:
        # Fall back to SQLite for local development
        base_dir = os.path.dirname(os.path.dirname(__file__))
        url = f"sqlite:///{os.path.join(base_dir, 'farm_pay.db')}"
        print(f"Using SQLite database: {url}")
    
    return url

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()