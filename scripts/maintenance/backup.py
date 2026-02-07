import os
import sys
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DatabaseBackup:
    def __init__(self, host: str = "localhost", port: int = 5432,
                 user: str = "postgres", password: str = "postgres",
                 db_name: str = "vitasense", backup_dir: str = "backups"):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db_name = db_name
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, backup_type: str = "full") -> Optional[Path]:
        """Create a database backup."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"{self.db_name}_{backup_type}_{timestamp}.sql"
            
            logger.info(f"Creating {backup_type} backup: {backup_file}")
            
            # Set environment variable for password
            env = os.environ.copy()
            env["PGPASSWORD"] = self.password
            
            # Build pg_dump command
            cmd = [
                "pg_dump",
                "-h", self.host,
                "-p", str(self.port),
                "-U", self.user,
                "-F", "c",  # Custom format
                "-b",  # Include large objects
                "-v",  # Verbose
                "-f", str(backup_file),
                self.db_name
            ]
            
            # Add additional options based on backup type
            if backup_type == "schema":
                cmd.extend(["--schema-only"])
            elif backup_type == "data":
                cmd.extend(["--data-only"])
            
            # Execute backup
            process = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                logger.info(f"Backup created successfully: {backup_file}")
                return backup_file
            else:
                logger.error(f"Backup failed: {process.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            return None

    def restore_backup(self, backup_file: Path) -> bool:
        """Restore database from backup."""
        try:
            if not backup_file.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_file}")
            
            logger.info(f"Restoring database from backup: {backup_file}")
            
            # Set environment variable for password
            env = os.environ.copy()
            env["PGPASSWORD"] = self.password
            
            # Build pg_restore command
            cmd = [
                "pg_restore",
                "-h", self.host,
                "-p", str(self.port),
                "-U", self.user,
                "-d", self.db_name,
                "-v",  # Verbose
                "-c",  # Clean (drop) database objects before recreating
                str(backup_file)
            ]
            
            # Execute restore
            process = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                logger.info("Database restored successfully")
                return True
            else:
                logger.error(f"Restore failed: {process.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to restore backup: {str(e)}")
            return False

    def cleanup_old_backups(self, days: int = 30) -> None:
        """Remove backups older than specified days."""
        try:
            logger.info(f"Cleaning up backups older than {days} days")
            current_time = datetime.now()
            
            for backup_file in self.backup_dir.glob("*.sql"):
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                age_days = (current_time - file_time).days
                
                if age_days > days:
                    logger.info(f"Removing old backup: {backup_file}")
                    backup_file.unlink()
                    
            logger.info("Backup cleanup completed")
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {str(e)}")
            raise

    def verify_backup(self, backup_file: Path) -> bool:
        """Verify backup file integrity."""
        try:
            if not backup_file.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_file}")
            
            logger.info(f"Verifying backup: {backup_file}")
            
            # Set environment variable for password
            env = os.environ.copy()
            env["PGPASSWORD"] = self.password
            
            # Build pg_restore command with --list option
            cmd = [
                "pg_restore",
                "-l",  # List contents
                str(backup_file)
            ]
            
            # Execute verification
            process = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                logger.info("Backup verification successful")
                return True
            else:
                logger.error(f"Backup verification failed: {process.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to verify backup: {str(e)}")
            return False

if __name__ == "__main__":
    # Get database configuration from environment variables
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "5432"))
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")
    db_name = os.getenv("DB_NAME", "vitasense")
    backup_dir = os.getenv("BACKUP_DIR", "backups")
    
    # Initialize backup manager
    backup = DatabaseBackup(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        db_name=db_name,
        backup_dir=backup_dir
    )
    
    # Create full backup
    backup_file = backup.create_backup(backup_type="full")
    
    if backup_file:
        # Verify backup
        if backup.verify_backup(backup_file):
            # Cleanup old backups
            backup.cleanup_old_backups() 