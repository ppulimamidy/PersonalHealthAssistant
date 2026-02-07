import os
import sys
from pathlib import Path
import logging
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from alembic.script.revision import Revision
from sqlalchemy import create_engine, inspect
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DatabaseMigration:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.alembic_cfg = Config()
        self.alembic_cfg.set_main_option("script_location", "migrations")
        self.alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        self.engine = create_engine(db_url)

    def init_migrations(self) -> None:
        """Initialize Alembic migrations if not already initialized."""
        try:
            if not Path("migrations").exists():
                logger.info("Initializing Alembic migrations")
                command.init(self.alembic_cfg, "migrations")
                logger.info("Alembic migrations initialized successfully")
            else:
                logger.info("Alembic migrations already initialized")
        except Exception as e:
            logger.error(f"Failed to initialize migrations: {str(e)}")
            raise

    def create_migration(self, message: str) -> None:
        """Create a new migration."""
        try:
            logger.info(f"Creating new migration: {message}")
            command.revision(self.alembic_cfg, message=message, autogenerate=True)
            logger.info("Migration created successfully")
        except Exception as e:
            logger.error(f"Failed to create migration: {str(e)}")
            raise

    def get_current_revision(self) -> Optional[str]:
        """Get the current database revision."""
        try:
            with self.engine.connect() as conn:
                context = MigrationContext.configure(conn)
                return context.get_current_revision()
        except Exception as e:
            logger.error(f"Failed to get current revision: {str(e)}")
            raise

    def get_head_revision(self) -> str:
        """Get the latest migration revision."""
        try:
            script = ScriptDirectory.from_config(self.alembic_cfg)
            return script.get_current_head()
        except Exception as e:
            logger.error(f"Failed to get head revision: {str(e)}")
            raise

    def get_pending_migrations(self) -> List[Revision]:
        """Get list of pending migrations."""
        try:
            current = self.get_current_revision()
            head = self.get_head_revision()
            script = ScriptDirectory.from_config(self.alembic_cfg)
            return list(script.iterate_revisions(current, head))
        except Exception as e:
            logger.error(f"Failed to get pending migrations: {str(e)}")
            raise

    def upgrade(self, revision: str = "head") -> None:
        """Upgrade database to specified revision."""
        try:
            logger.info(f"Upgrading database to revision: {revision}")
            command.upgrade(self.alembic_cfg, revision)
            logger.info("Database upgrade completed successfully")
        except Exception as e:
            logger.error(f"Failed to upgrade database: {str(e)}")
            raise

    def downgrade(self, revision: str) -> None:
        """Downgrade database to specified revision."""
        try:
            logger.info(f"Downgrading database to revision: {revision}")
            command.downgrade(self.alembic_cfg, revision)
            logger.info("Database downgrade completed successfully")
        except Exception as e:
            logger.error(f"Failed to downgrade database: {str(e)}")
            raise

    def check_migrations(self) -> None:
        """Check for pending migrations and apply them."""
        try:
            pending = self.get_pending_migrations()
            if pending:
                logger.info(f"Found {len(pending)} pending migrations")
                self.upgrade()
            else:
                logger.info("No pending migrations found")
        except Exception as e:
            logger.error(f"Failed to check migrations: {str(e)}")
            raise

if __name__ == "__main__":
    # Get database URL from environment variable
    db_url = os.getenv("DATABASE_URL", "postgresql://admin:admin@localhost:5433/vitasense")
    
    # Initialize and run migrations
    migration = DatabaseMigration(db_url)
    migration.init_migrations()
    migration.check_migrations() 