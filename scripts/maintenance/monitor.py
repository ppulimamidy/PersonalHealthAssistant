import os
import sys
import psycopg2
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DatabaseMonitor:
    def __init__(self, host: str = "localhost", port: int = 5432,
                 user: str = "postgres", password: str = "postgres",
                 db_name: str = "vitasense"):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db_name = db_name
        self.metrics_dir = Path("metrics")
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

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

    def check_connection_pool(self) -> Dict:
        """Check connection pool status."""
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT count(*) as total_connections,
                           count(*) FILTER (WHERE state = 'active') as active_connections,
                           count(*) FILTER (WHERE state = 'idle') as idle_connections
                    FROM pg_stat_activity
                    WHERE datname = %s
                """, (self.db_name,))
                return dict(zip(['total', 'active', 'idle'], cur.fetchone()))
        except Exception as e:
            logger.error(f"Failed to check connection pool: {str(e)}")
            raise
        finally:
            conn.close()

    def check_table_sizes(self) -> List[Dict]:
        """Check sizes of all tables."""
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT schemaname, tablename,
                           pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) as total_size,
                           pg_size_pretty(pg_relation_size(schemaname || '.' || tablename)) as table_size,
                           pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename) - 
                                        pg_relation_size(schemaname || '.' || tablename)) as index_size
                    FROM pg_tables
                    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                    ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC
                """)
                return [dict(zip(['schema', 'table', 'total_size', 'table_size', 'index_size'], row))
                       for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to check table sizes: {str(e)}")
            raise
        finally:
            conn.close()

    def check_index_usage(self) -> List[Dict]:
        """Check index usage statistics."""
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT schemaname, tablename, indexname,
                           idx_scan as number_of_scans,
                           idx_tup_read as tuples_read,
                           idx_tup_fetch as tuples_fetched
                    FROM pg_stat_user_indexes
                    ORDER BY idx_scan DESC
                """)
                return [dict(zip(['schema', 'table', 'index', 'scans', 'tuples_read', 'tuples_fetched'], row))
                       for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to check index usage: {str(e)}")
            raise
        finally:
            conn.close()

    def check_long_running_queries(self) -> List[Dict]:
        """Check for long-running queries."""
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT pid, age(clock_timestamp(), query_start) as duration,
                           query, state
                    FROM pg_stat_activity
                    WHERE state != 'idle'
                    AND query NOT ILIKE '%pg_stat_activity%'
                    ORDER BY duration DESC
                """)
                return [dict(zip(['pid', 'duration', 'query', 'state'], row))
                       for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to check long-running queries: {str(e)}")
            raise
        finally:
            conn.close()

    def check_vacuum_status(self) -> List[Dict]:
        """Check vacuum status of tables."""
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT schemaname, tablename,
                           last_vacuum, last_autovacuum,
                           last_analyze, last_autoanalyze
                    FROM pg_stat_user_tables
                    ORDER BY last_vacuum NULLS FIRST
                """)
                return [dict(zip(['schema', 'table', 'last_vacuum', 'last_autovacuum',
                                'last_analyze', 'last_autoanalyze'], row))
                       for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to check vacuum status: {str(e)}")
            raise
        finally:
            conn.close()

    def check_locks(self) -> List[Dict]:
        """Check for locks in the database."""
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT blocked_locks.pid AS blocked_pid,
                           blocking_locks.pid AS blocking_pid,
                           blocked_activity.usename AS blocked_user,
                           blocking_activity.usename AS blocking_user,
                           blocked_activity.query AS blocked_statement,
                           blocking_activity.query AS blocking_statement
                    FROM pg_catalog.pg_locks blocked_locks
                    JOIN pg_catalog.pg_locks blocking_locks
                        ON blocking_locks.locktype = blocked_locks.locktype
                        AND blocking_locks.DATABASE IS NOT DISTINCT FROM blocked_locks.DATABASE
                        AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
                        AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
                        AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
                        AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
                        AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
                        AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
                        AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
                        AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
                        AND blocking_locks.pid != blocked_locks.pid
                    JOIN pg_catalog.pg_stat_activity blocked_activity
                        ON blocked_activity.pid = blocked_locks.pid
                    JOIN pg_catalog.pg_stat_activity blocking_activity
                        ON blocking_activity.pid = blocking_locks.pid
                    WHERE NOT blocked_locks.GRANTED
                """)
                return [dict(zip(['blocked_pid', 'blocking_pid', 'blocked_user', 'blocking_user',
                                'blocked_statement', 'blocking_statement'], row))
                       for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to check locks: {str(e)}")
            raise
        finally:
            conn.close()

    def save_metrics(self, metrics: Dict) -> None:
        """Save metrics to a JSON file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            metrics_file = self.metrics_dir / f"metrics_{timestamp}.json"
            
            with open(metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2, default=str)
                
            logger.info(f"Metrics saved to {metrics_file}")
        except Exception as e:
            logger.error(f"Failed to save metrics: {str(e)}")
            raise

    def collect_metrics(self) -> Dict:
        """Collect all database metrics."""
        try:
            metrics = {
                'timestamp': datetime.now(),
                'connection_pool': self.check_connection_pool(),
                'table_sizes': self.check_table_sizes(),
                'index_usage': self.check_index_usage(),
                'long_running_queries': self.check_long_running_queries(),
                'vacuum_status': self.check_vacuum_status(),
                'locks': self.check_locks()
            }
            
            self.save_metrics(metrics)
            return metrics
        except Exception as e:
            logger.error(f"Failed to collect metrics: {str(e)}")
            raise

if __name__ == "__main__":
    # Get database configuration from environment variables
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "5432"))
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")
    db_name = os.getenv("DB_NAME", "vitasense")
    
    # Initialize monitor
    monitor = DatabaseMonitor(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        db_name=db_name
    )
    
    # Collect and save metrics
    monitor.collect_metrics() 