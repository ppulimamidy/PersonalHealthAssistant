import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
from alembic import context
from common.config.settings import get_settings
from common.models.base import Base

# Import ALL models so they register with Base.metadata
try:
    from apps.auth.models.user import *
except ImportError:
    pass
try:
    from apps.auth.models.session import *
except ImportError:
    pass
try:
    from apps.auth.models.roles import *
except ImportError:
    pass
try:
    from apps.auth.models.mfa import *
except ImportError:
    pass
try:
    from apps.auth.models.audit import *
except ImportError:
    pass
try:
    from apps.auth.models.consent import *
except ImportError:
    pass

settings = get_settings()
config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Include schemas
SCHEMAS = [
    "auth",
    "device_data",
    "medical_records",
    "nutrition",
    "genomics",
    "doctor_collaboration",
    "consent_audit",
    "ecommerce",
    "explainability",
]


def include_name(name, type_, parent_names):
    if type_ == "schema":
        return name in SCHEMAS or name is None
    return True


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        include_schemas=True,
        include_name=include_name,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        # Create schemas first
        for schema in SCHEMAS:
            connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        connection.commit()
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_name=include_name,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
