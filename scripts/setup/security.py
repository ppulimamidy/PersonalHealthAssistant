import os
import sys
import psycopg2
import logging
from pathlib import Path
from typing import List, Dict
import secrets
import string
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parents[2] / '.env'
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DatabaseSecurity:
    def __init__(self, host: str = None, port: int = None,
                 user: str = None, password: str = None,
                 db_name: str = None):
        # Load configuration from environment variables with defaults
        self.host = host or os.getenv("DB_HOST", "localhost")
        self.port = port or int(os.getenv("DB_PORT", "5432"))
        self.user = user or os.getenv("DB_USER", "postgres")
        self.password = password or os.getenv("DB_PASSWORD", "postgres")
        self.db_name = db_name or os.getenv("DB_NAME", "vitasense")
        
        # Load SSL configuration
        self.ssl_cert_file = os.getenv("DB_SSL_CERT_FILE", "/etc/ssl/certs/server.crt")
        self.ssl_key_file = os.getenv("DB_SSL_KEY_FILE", "/etc/ssl/private/server.key")
        self.ssl_ca_file = os.getenv("DB_SSL_CA_FILE", "/etc/ssl/certs/ca.crt")
        
        # Load password policy configuration
        self.password_min_length = int(os.getenv("DB_PASSWORD_MIN_LENGTH", "12"))
        self.password_max_length = int(os.getenv("DB_PASSWORD_MAX_LENGTH", "128"))
        self.password_reuse_interval = int(os.getenv("DB_PASSWORD_REUSE_INTERVAL", "365"))
        self.password_reuse_max = int(os.getenv("DB_PASSWORD_REUSE_MAX", "3"))

    def get_connection(self) -> psycopg2.extensions.connection:
        """Create a database connection."""
        try:
            return psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                dbname=self.db_name
            )
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise

    def generate_password(self, length: int = 16) -> str:
        """Generate a secure random password."""
        alphabet = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def create_roles(self) -> None:
        """Create database roles with appropriate permissions."""
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                # Create application role
                cur.execute("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'vitasense_app') THEN
                            CREATE ROLE vitasense_app WITH LOGIN PASSWORD %s;
                        END IF;
                    END
                    $$;
                """, (self.generate_password(),))
                
                # Create readonly role
                cur.execute("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'vitasense_readonly') THEN
                            CREATE ROLE vitasense_readonly WITH LOGIN PASSWORD %s;
                        END IF;
                    END
                    $$;
                """, (self.generate_password(),))
                
                # Create backup role
                cur.execute("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'vitasense_backup') THEN
                            CREATE ROLE vitasense_backup WITH LOGIN PASSWORD %s;
                        END IF;
                    END
                    $$;
                """, (self.generate_password(),))
                
            logger.info("Database roles created successfully")
        except Exception as e:
            logger.error(f"Failed to create roles: {str(e)}")
            raise
        finally:
            conn.close()

    def grant_permissions(self) -> None:
        """Grant appropriate permissions to roles."""
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                # Grant permissions to application role
                cur.execute("""
                    GRANT CONNECT ON DATABASE vitasense TO vitasense_app;
                    GRANT USAGE ON SCHEMA public TO vitasense_app;
                    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO vitasense_app;
                    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO vitasense_app;
                    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO vitasense_app;
                    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO vitasense_app;
                """)
                
                # Grant permissions to readonly role
                cur.execute("""
                    GRANT CONNECT ON DATABASE vitasense TO vitasense_readonly;
                    GRANT USAGE ON SCHEMA public TO vitasense_readonly;
                    GRANT SELECT ON ALL TABLES IN SCHEMA public TO vitasense_readonly;
                    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO vitasense_readonly;
                """)
                
                # Grant permissions to backup role
                cur.execute("""
                    GRANT CONNECT ON DATABASE vitasense TO vitasense_backup;
                    GRANT USAGE ON SCHEMA public TO vitasense_backup;
                    GRANT SELECT ON ALL TABLES IN SCHEMA public TO vitasense_backup;
                    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO vitasense_backup;
                """)
                
            logger.info("Permissions granted successfully")
        except Exception as e:
            logger.error(f"Failed to grant permissions: {str(e)}")
            raise
        finally:
            conn.close()

    def configure_ssl(self) -> None:
        """Configure SSL settings for the database."""
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                # Configure SSL settings
                cur.execute("""
                    ALTER SYSTEM SET ssl = 'on';
                    ALTER SYSTEM SET ssl_cert_file = %s;
                    ALTER SYSTEM SET ssl_key_file = %s;
                    ALTER SYSTEM SET ssl_ca_file = %s;
                    ALTER SYSTEM SET ssl_prefer_server_ciphers = 'on';
                """, (self.ssl_cert_file, self.ssl_key_file, self.ssl_ca_file))
            logger.info("SSL configuration completed")
        except Exception as e:
            logger.error(f"Failed to configure SSL: {str(e)}")
            raise
        finally:
            conn.close()

    def configure_password_policy(self) -> None:
        """Configure password policy settings."""
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                # Configure password policy
                cur.execute("""
                    ALTER SYSTEM SET password_encryption = 'scram-sha-256';
                    ALTER SYSTEM SET password_min_length = %s;
                    ALTER SYSTEM SET password_max_length = %s;
                    ALTER SYSTEM SET password_reuse_interval = %s;
                    ALTER SYSTEM SET password_reuse_max = %s;
                """, (
                    self.password_min_length,
                    self.password_max_length,
                    self.password_reuse_interval,
                    self.password_reuse_max
                ))
            logger.info("Password policy configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure password policy: {str(e)}")
            raise
        finally:
            conn.close()

    def configure_audit_logging(self) -> None:
        """Configure audit logging settings."""
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                # Configure audit logging
                cur.execute("""
                    ALTER SYSTEM SET log_connections = 'on';
                    ALTER SYSTEM SET log_disconnections = 'on';
                    ALTER SYSTEM SET log_statement = 'ddl';
                    ALTER SYSTEM SET log_duration = 'on';
                    ALTER SYSTEM SET log_lock_waits = 'on';
                    ALTER SYSTEM SET log_temp_files = '0';
                    ALTER SYSTEM SET log_autovacuum_min_duration = '0';
                """)
            logger.info("Audit logging configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure audit logging: {str(e)}")
            raise
        finally:
            conn.close()

    def setup_row_level_security(self) -> None:
        """Set up row-level security policies."""
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                # Enable RLS on tables
                cur.execute("""
                    ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;
                    ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
                    ALTER TABLE public.medical_records ENABLE ROW LEVEL SECURITY;
                    ALTER TABLE public.health_metrics ENABLE ROW LEVEL SECURITY;
                """)
                
                # Create RLS policies
                cur.execute("""
                    CREATE POLICY users_policy ON auth.users
                        USING (auth.uid() = id)
                        WITH CHECK (auth.uid() = id);
                        
                    CREATE POLICY profiles_policy ON public.user_profiles
                        USING (user_id = auth.uid())
                        WITH CHECK (user_id = auth.uid());
                        
                    CREATE POLICY records_policy ON public.medical_records
                        USING (user_id = auth.uid())
                        WITH CHECK (user_id = auth.uid());
                        
                    CREATE POLICY metrics_policy ON public.health_metrics
                        USING (user_id = auth.uid())
                        WITH CHECK (user_id = auth.uid());
                """)
                
            logger.info("Row-level security configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure row-level security: {str(e)}")
            raise
        finally:
            conn.close()

    def run_security_setup(self) -> None:
        """Run the complete security setup process."""
        try:
            logger.info("Starting security setup")
            self.create_roles()
            self.grant_permissions()
            self.configure_ssl()
            self.configure_password_policy()
            self.configure_audit_logging()
            self.setup_row_level_security()
            logger.info("Security setup completed successfully")
        except Exception as e:
            logger.error(f"Security setup failed: {str(e)}")
            raise

if __name__ == "__main__":
    # Initialize security setup with environment variables
    security = DatabaseSecurity()
    
    # Run security setup
    security.run_security_setup() 