import os
import platform
import subprocess
import shutil
import sys
import time
from typing import List, Dict, Optional
from pathlib import Path
import logging

# Initialize logger at the top
logger = logging.getLogger("setup_agent")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)

log_file = "setup_agent.log"

def log(msg: str, level: str = "INFO") -> None:
    """Log message to console and file with timestamp."""
    timestamp = subprocess.check_output(["date", "+%Y-%m-%d %H:%M:%S"]).decode().strip()
    formatted_msg = f"[{timestamp}] [{level}] {msg}"
    print(formatted_msg)
    with open(log_file, "a") as f:
        f.write(f"{formatted_msg}\n")

def run_cmd(cmd: str, check: bool = False, retries: int = 3, delay: int = 5) -> Optional[subprocess.CompletedProcess]:
    """Run shell command with proper error handling and retries."""
    for attempt in range(retries):
        try:
            result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
            if result.returncode == 0:
                return result
            log(f"Command failed (attempt {attempt + 1}/{retries}): {cmd}\nError: {result.stderr}", "WARNING")
            if attempt < retries - 1:
                time.sleep(delay)
        except subprocess.CalledProcessError as e:
            log(f"Command failed (attempt {attempt + 1}/{retries}): {cmd}\nError: {e.stderr}", "ERROR")
            if attempt < retries - 1:
                time.sleep(delay)
        except Exception as e:
            log(f"Unexpected error running command {cmd}: {str(e)}", "ERROR")
            if attempt < retries - 1:
                time.sleep(delay)
    return None

def is_installed(tool: str) -> bool:
    """Check if a tool is installed and accessible."""
    return shutil.which(tool) is not None

def get_package_manager() -> Dict[str, str]:
    """Get the appropriate package manager for the OS."""
    os_type = platform.system().lower()
    if os_type == "darwin":
        return {
            "install": "brew install",
            "update": "brew update",
            "python": "python3",
            "pip": "pip3",
            "service_start": "brew services start",
            "service_stop": "brew services stop",
            "service_status": "brew services list"
        }
    elif os_type == "linux":
        return {
            "install": "sudo apt-get install -y",
            "update": "sudo apt-get update",
            "python": "python3",
            "pip": "pip3",
            "service_start": "sudo systemctl start",
            "service_stop": "sudo systemctl stop",
            "service_status": "sudo systemctl status"
        }
    elif os_type == "windows":
        return {
            "install": "choco install -y",
            "update": "choco upgrade all -y",
            "python": "python",
            "pip": "pip",
            "service_start": "net start",
            "service_stop": "net stop",
            "service_status": "sc query"
        }
    else:
        raise OSError(f"Unsupported operating system: {os_type}")

def install_package(pkg: str) -> None:
    """Install a system package using the appropriate package manager."""
    try:
        pkg_manager = get_package_manager()
        log(f"📦 Installing {pkg}...")
        run_cmd(f"{pkg_manager['update']} && {pkg_manager['install']} {pkg}", check=True)
    except Exception as e:
        log(f"Failed to install {pkg}: {str(e)}", "ERROR")

def install_pip_package(pkg: str) -> None:
    """Install a Python package using pip."""
    try:
        pkg_manager = get_package_manager()
        log(f"🐍 Installing Python package: {pkg}")
        run_cmd(f"{pkg_manager['pip']} install {pkg}", check=True)
    except Exception as e:
        log(f"Failed to install Python package {pkg}: {str(e)}", "ERROR")

def setup_python_environment() -> None:
    """Set up Python virtual environment and install dependencies."""
    log("Setting up Python virtual environment...")
    pkg_manager = get_package_manager()
    
    # Create virtual environment using python3
    venv_cmd = f"{pkg_manager['python']} -m venv venv"
    if not run_cmd(venv_cmd, check=True):
        log("Failed to create virtual environment", "ERROR")
        return
    
    # Activate virtual environment and install requirements
    if platform.system() == "Windows":
        activate_cmd = ".\\venv\\Scripts\\activate"
    else:
        activate_cmd = "source venv/bin/activate"
    
    # Install requirements
    pip_cmd = f"{activate_cmd} && {pkg_manager['pip']} install -r requirements.txt"
    if not run_cmd(pip_cmd, check=True):
        log("Failed to install requirements", "ERROR")
        return
    
    log("✅ Python virtual environment setup completed")

def check_postgres_running() -> bool:
    """Check if PostgreSQL is already running on the default port."""
    try:
        # Check if port 5432 is in use
        if platform.system() == "Darwin":
            result = run_cmd("lsof -i :5432", check=False)
        elif platform.system() == "Linux":
            result = run_cmd("netstat -tuln | grep :5432", check=False)
        elif platform.system() == "Windows":
            result = run_cmd("netstat -ano | findstr :5432", check=False)
        
        return result is not None and result.returncode == 0
    except Exception:
        return False

def get_postgres_processes() -> List[str]:
    """Get list of running PostgreSQL processes."""
    try:
        if platform.system() == "Darwin":
            # Get process IDs using lsof
            result = run_cmd("lsof -i :5432 | grep LISTEN", check=False)
            if result and result.returncode == 0:
                return [line.split()[1] for line in result.stdout.splitlines()]
        elif platform.system() == "Linux":
            result = run_cmd("pgrep -f postgres", check=False)
            if result and result.returncode == 0:
                return result.stdout.splitlines()
        elif platform.system() == "Windows":
            result = run_cmd("tasklist /FI \"IMAGENAME eq postgres.exe\" /NH", check=False)
            if result and result.returncode == 0:
                return [line.split()[1] for line in result.stdout.splitlines()]
    except Exception:
        pass
    return []

def stop_postgres_service() -> None:
    """Stop PostgreSQL service if it's running."""
    log("Checking for existing PostgreSQL instances...")
    
    # First check if PostgreSQL is running on port 5432
    if not check_postgres_running():
        log("No PostgreSQL instances found running on port 5432")
        return
        
    # Get list of running PostgreSQL processes
    pg_processes = get_postgres_processes()
    if not pg_processes:
        log("No PostgreSQL processes found")
        return
        
    log(f"Found {len(pg_processes)} PostgreSQL processes. Attempting to stop...")
    
    if platform.system() == "Darwin":
        # Try to stop Homebrew services first
        run_cmd("brew services stop postgresql@14", check=False)
        run_cmd("brew services stop postgresql", check=False)
        
        # If processes are still running, try to kill them
        if get_postgres_processes():
            for pid in pg_processes:
                try:
                    run_cmd(f"kill -15 {pid}", check=False)
                except Exception:
                    pass
            
            # Wait a bit and check if processes are still running
            time.sleep(2)
            if get_postgres_processes():
                # If still running, try force kill
                for pid in get_postgres_processes():
                    try:
                        run_cmd(f"kill -9 {pid}", check=False)
                    except Exception:
                        pass
    
    elif platform.system() == "Linux":
        run_cmd("sudo systemctl stop postgresql", check=False)
        # If still running, try to kill processes
        if get_postgres_processes():
            for pid in get_postgres_processes():
                try:
                    run_cmd(f"sudo kill -15 {pid}", check=False)
                except Exception:
                    pass
    
    elif platform.system() == "Windows":
        run_cmd("net stop postgresql", check=False)
        # If still running, try to kill processes
        if get_postgres_processes():
            for pid in get_postgres_processes():
                try:
                    run_cmd(f"taskkill /F /PID {pid}", check=False)
                except Exception:
                    pass
    
    # Wait for the service to stop
    time.sleep(5)
    
    # Verify it's stopped
    if check_postgres_running():
        log("Warning: Could not stop existing PostgreSQL instance", "WARNING")
    else:
        log("Successfully stopped existing PostgreSQL instance")

def setup_postgresql() -> None:
    """Set up and start PostgreSQL service."""
    log("Setting up PostgreSQL...")
    pkg_manager = get_package_manager()
    
    # First check and stop any existing PostgreSQL instances
    stop_postgres_service()
    
    # Install PostgreSQL
    if platform.system() == "Darwin":
        install_package("postgresql@14")
        
        # Initialize PostgreSQL data directory if it doesn't exist
        data_dir = "/opt/homebrew/var/postgresql@14"
        if not os.path.exists(data_dir):
            log("Initializing PostgreSQL data directory...")
            run_cmd(f"initdb -D {data_dir}", check=True)
        
        # Create pg_hba.conf with proper authentication
        pg_hba_path = os.path.join(data_dir, "pg_hba.conf")
        if os.path.exists(pg_hba_path):
            with open(pg_hba_path, "w") as f:
                f.write("""# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                trust
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
""")
        
        # Start PostgreSQL service with proper permissions
        log("Starting PostgreSQL service...")
        run_cmd("brew services start postgresql@14", check=True)
        
        # Wait for PostgreSQL to start and create socket
        max_retries = 10
        socket_path = "/tmp/.s.PGSQL.5432"
        for i in range(max_retries):
            if os.path.exists(socket_path):
                break
            time.sleep(2)
            if i == max_retries - 1:
                log("Failed to create PostgreSQL socket", "ERROR")
                return
        
        # Wait for PostgreSQL to be ready
        max_retries = 10
        for i in range(max_retries):
            try:
                # First try to connect as the current user
                result = run_cmd("psql postgres -c 'SELECT 1'", check=False)
                if result and result.returncode == 0:
                    # Create postgres role if it doesn't exist
                    create_role_cmd = "psql postgres -c \"DO \\$\\$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'postgres') THEN CREATE ROLE postgres WITH SUPERUSER LOGIN; END IF; END \\$\\$;\""
                    run_cmd(create_role_cmd, check=False)
                    break
            except Exception:
                pass
            time.sleep(2)
            if i == max_retries - 1:
                log("Failed to connect to PostgreSQL after multiple attempts", "ERROR")
                return
        
        # Now try to connect as postgres user
        max_retries = 10
        for i in range(max_retries):
            try:
                result = run_cmd("psql -U postgres -c 'SELECT 1'", check=False)
                if result and result.returncode == 0:
                    break
            except Exception:
                pass
            time.sleep(2)
            if i == max_retries - 1:
                log("Failed to connect as postgres user after multiple attempts", "ERROR")
                return
    
    elif platform.system() == "Linux":
        install_package("postgresql")
        run_cmd(f"{pkg_manager['service_start']} postgresql", check=True)
    elif platform.system() == "Windows":
        install_package("postgresql")
        run_cmd(f"{pkg_manager['service_start']} postgresql", check=True)
    
    # Create database if it doesn't exist
    create_db_cmd = """psql -U postgres -c "DO \\$\\$ 
    BEGIN 
        IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'vitasense') THEN
            CREATE DATABASE vitasense;
        END IF;
    END \\$\\$;" """
    run_cmd(create_db_cmd, check=False)
    
    log("✅ PostgreSQL setup completed")

def check_docker() -> bool:
    """Check if Docker is running and properly configured."""
    logger.info("Checking Docker status...")
    
    # First check if Docker is installed
    if not run_cmd("docker --version", check=False):
        logger.error("❌ Docker is not installed. Please install Docker Desktop first.")
        return False
    
    # Check if Docker daemon is running
    try:
        result = run_cmd("docker info", check=False)
        if not result:
            logger.error("❌ Docker daemon is not running.")
            logger.info("Please follow these steps:")
            logger.info("1. Open Docker Desktop application")
            logger.info("2. Wait for Docker Desktop to fully start")
            logger.info("3. Make sure you're signed in to Docker Desktop")
            logger.info("4. Try running the setup script again")
            return False
            
        # Check if user is authenticated
        result = run_cmd("docker login", check=False)
        if not result:
            logger.warning("⚠️ You may not be authenticated with Docker Hub.")
            logger.info("Please sign in to Docker Desktop or run 'docker login'")
            return False
            
        logger.info("✅ Docker is running and properly configured")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking Docker status: {str(e)}")
        logger.info("Please ensure Docker Desktop is running and you're signed in.")
        return False

def setup_docker_compose() -> None:
    """Set up Docker Compose services."""
    if not check_docker():
        logger.error("❌ Docker setup failed. Please ensure Docker Desktop is running and you're signed in.")
        return False
        
    logger.info("Setting up Docker Compose services...")
    
    # Create docker-compose.yml if it doesn't exist
    if not os.path.exists("docker-compose.yml"):
        logger.info("Creating docker-compose.yml...")
        docker_compose_content = """name: vitasense

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: vitasense
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: admin
    ports:
      - "5433:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admin -d vitasense"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s

  postgrest:
    image: postgrest/postgrest:v11.2.0
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      PGRST_DB_URI: postgres://admin:admin@postgres:5432/vitasense
      PGRST_DB_SCHEMA: public
      PGRST_DB_ANON_ROLE: anon
      PGRST_JWT_SECRET: "your-jwt-secret"
    ports:
      - "3000:3000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s

  zookeeper:
    image: bitnami/zookeeper:latest
    environment:
      ALLOW_ANONYMOUS_LOGIN: "yes"
      ZOO_4LW_COMMANDS_WHITELIST: "*"
      ZOO_SERVERS: "server.1=zookeeper:2888:3888"
      ZOO_SERVER_ID: "1"
    ports:
      - "2181:2181"
      - "2888:2888"
      - "3888:3888"
    volumes:
      - zookeeper_data:/bitnami/zookeeper
    healthcheck:
      test: ["CMD-SHELL", "echo srvr | nc localhost 2181 || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  kafka:
    image: bitnami/kafka:latest
    depends_on:
      zookeeper:
        condition: service_healthy
    environment:
      KAFKA_CFG_ZOOKEEPER_CONNECT: "zookeeper:2181"
      KAFKA_CFG_ADVERTISED_LISTENERS: "PLAINTEXT://kafka:9092"
      ALLOW_PLAINTEXT_LISTENER: "yes"
      KAFKA_CFG_AUTO_CREATE_TOPICS_ENABLE: "true"
      KAFKA_CFG_DELETE_TOPIC_ENABLE: "true"
    ports:
      - "9092:9092"
    volumes:
      - kafka_data:/bitnami/kafka
    healthcheck:
      test: ["CMD-SHELL", "kafka-topics.sh --bootstrap-server localhost:9092 --list"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s

  prometheus:
    image: prom/prometheus
    ports:
      - "9091:9090"
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:9090/-/healthy"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    depends_on:
      prometheus:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:3000/api/health"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s

  jaeger:
    image: jaegertracing/all-in-one
    ports:
      - "16686:16686"
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:16686/api/services"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s

  vitasense-api:
    profiles: ["api"]
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    depends_on:
      postgres:
        condition: service_healthy
      kafka:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s

volumes:
  pgdata:
  zookeeper_data:
  kafka_data:
"""
        with open("docker-compose.yml", "w") as f:
            f.write(docker_compose_content)
        logger.info("✅ Created docker-compose.yml")
    
    # Pull Docker images
    logger.info("Pulling Docker images...")
    if not run_cmd("docker-compose pull", check=False):
        logger.error("❌ Failed to pull Docker images")
        return False
    
    # Start services
    logger.info("Starting Docker services...")
    if not run_cmd("docker-compose up -d", check=False):
        logger.error("❌ Failed to start Docker services")
        return False
    
    logger.info("✅ Docker services started successfully")
    return True

def setup_git_hooks() -> None:
    """Set up Git hooks and pre-commit configuration."""
    log("Setting up Git hooks...")
    install_pip_package("pre-commit")
    run_cmd("pre-commit install", check=True)
    log("✅ Git hooks setup completed")

def create_env_file() -> None:
    """Create .env file with default configuration."""
    env_content = """# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=vitasense

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
"""
    with open(".env", "w") as f:
        f.write(env_content)
    log("✅ Created .env file with default configuration")

def install_tools() -> None:
    """Install all required tools and dependencies."""
    try:
        log("🚀 Starting development environment setup...")
        
        # System tools
        system_tools = ["git", "curl", "wget", "make", "unzip", "jq"]
        for tool in system_tools:
            if not is_installed(tool):
                install_package(tool)
            else:
                log(f"✅ {tool} already installed.")

        # Create .env file
        create_env_file()

        # Python setup
        setup_python_environment()

        # PostgreSQL setup
        setup_postgresql()

        # Docker setup
        if not is_installed("docker"):
            install_package("docker")
        if not is_installed("docker-compose"):
            install_package("docker-compose")

        # Development tools
        install_pip_package("black")
        install_pip_package("pylint")
        install_pip_package("mypy")
        install_pip_package("pytest")
        install_pip_package("pytest-asyncio")
        install_pip_package("pytest-cov")

        # Project dependencies
        install_pip_package("fastapi")
        install_pip_package("uvicorn")
        install_pip_package("sqlalchemy")
        install_pip_package("psycopg2-binary")
        install_pip_package("python-jose")
        install_pip_package("passlib")
        install_pip_package("python-multipart")
        install_pip_package("pydantic")
        install_pip_package("python-dotenv")
        install_pip_package("httpx")
        install_pip_package("redis")
        install_pip_package("kafka-python")
        install_pip_package("duckdb")
        install_pip_package("qdrant-client")
        install_pip_package("langchain")

        # Setup Docker Compose
        setup_docker_compose()

        # Setup Git hooks
        setup_git_hooks()

        log("✅ Development environment setup completed successfully!")
        log("Next steps:")
        log("1. Activate virtual environment: source venv/bin/activate (Unix) or .\\venv\\Scripts\\activate (Windows)")
        log("2. Start Docker services: docker-compose up -d")
        log("3. Run database migrations: python scripts/migration/run_migrations.py")
        log("4. Start development server: uvicorn apps.main:app --reload")

    except Exception as e:
        log(f"❌ Setup failed: {str(e)}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    install_tools()
