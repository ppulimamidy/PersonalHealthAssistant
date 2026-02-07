# Scripts Directory - Setup and Maintenance Tools

This directory contains all the scripts needed to set up, maintain, and troubleshoot the Personal Health Assistant project.

## 🚀 Quick Start for New Developers

### Option 1: One-Command Setup (Recommended)
```bash
# From project root
./setup.sh
```

### Option 2: Python Master Script
```bash
# From project root
python scripts/setup_master.py
```

### Option 3: Manual Setup
```bash
# Check prerequisites
python scripts/setup_master.py --check-only

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start services
docker-compose up -d

# Verify setup
python scripts/test_setup.py
```

## 📁 Script Organization

### Root Level Scripts

#### `setup.sh` - One-Command Setup Script
- **Purpose**: Complete automated setup for new developers
- **Usage**: `./setup.sh`
- **What it does**:
  - Checks prerequisites (Docker, Python, Git)
  - Sets up Python virtual environment
  - Installs dependencies
  - Starts all Docker services
  - Verifies everything is working
  - Provides next steps

#### `scripts/setup_master.py` - Python Master Setup
- **Purpose**: Comprehensive setup orchestration with detailed logging
- **Usage**: `python scripts/setup_master.py`
- **Features**:
  - Step-by-step setup with error handling
  - Detailed progress reporting
  - Prerequisites checking
  - Service verification
  - Test execution

### Setup Directory (`scripts/setup/`)

#### `scripts/setup/db_setup.py` - Database Setup
- **Purpose**: Initialize and configure the database
- **Usage**: `python scripts/setup/db_setup.py`
- **What it does**:
  - Creates database schema
  - Sets up extensions
  - Configures RLS policies
  - Seeds initial data

#### `scripts/setup/check_extensions.py` - Extension Verification
- **Purpose**: Verify PostgreSQL extensions are working
- **Usage**: `python scripts/setup/check_extensions.py`
- **What it does**:
  - Checks if all required extensions are installed
  - Tests extension functionality
  - Reports any issues

#### `scripts/setup/security.py` - Security Configuration
- **Purpose**: Set up security policies and configurations
- **Usage**: `python scripts/setup/security.py`
- **What it does**:
  - Configures RLS policies
  - Sets up authentication
  - Configures permissions

### Extensions Directory (`scripts/setup/extensions/`)

#### `01_extensions.sql` - PostgreSQL Extensions
- **Purpose**: Install and configure PostgreSQL extensions
- **Contains**:
  - TimescaleDB for time-series data
  - pg_trgm for fuzzy text search
  - pgcrypto for encryption
  - Custom health analytics functions

#### `02_auth_setup.sql` - Authentication Setup
- **Purpose**: Set up authentication and authorization
- **Contains**:
  - User roles and permissions
  - Auth schema configuration
  - RLS policy setup

### Utility Scripts

#### `scripts/setup_venv.py` - Virtual Environment Management
- **Purpose**: Create, manage, and validate Python virtual environment
- **Usage**: `python scripts/setup_venv.py [command]`
- **Commands**:
  - `python scripts/setup_venv.py` - Complete setup (create + install + validate)
  - `python scripts/setup_venv.py create` - Create virtual environment only
  - `python scripts/setup_venv.py validate` - Check virtual environment status
  - `python scripts/setup_venv.py install` - Install requirements only
  - `python scripts/setup_venv.py upgrade-pip` - Upgrade pip in venv
- **Features**:
  - Automatic virtual environment creation
  - Dependency installation
  - Environment validation
  - Cross-platform support (Windows, macOS, Linux)
  - Detailed status reporting

#### `scripts/test_setup.py` - Comprehensive Testing
- **Purpose**: Verify the entire setup is working
- **Usage**: `python scripts/test_setup.py`
- **Tests**:
  - Database connectivity
  - API endpoints
  - Service health
  - Extension functionality
  - Data integrity

#### `scripts/setup_prerequisites.sh` - Prerequisites Installation
- **Purpose**: Install required system dependencies
- **Usage**: `./scripts/setup_prerequisites.sh`
- **Installs**:
  - Docker and Docker Compose
  - Python 3.9+
  - Git
  - System dependencies

#### `scripts/quick_setup.py` - Quick Setup
- **Purpose**: Fast setup for experienced developers
- **Usage**: `python scripts/quick_setup.py`
- **What it does**:
  - Minimal setup with basic verification
  - Skips detailed testing
  - Assumes prerequisites are installed

### Troubleshooting Scripts

#### `scripts/fix_supabase_connection.py` - Connection Fixes
- **Purpose**: Fix common Supabase connection issues
- **Usage**: `python scripts/fix_supabase_connection.py`
- **Fixes**:
  - Network connectivity issues
  - Authentication problems
  - Configuration errors

#### `scripts/wake_up_supabase.py` - Service Recovery
- **Purpose**: Restart and recover Supabase services
- **Usage**: `python scripts/wake_up_supabase.py`
- **What it does**:
  - Restarts failed services
  - Clears stuck connections
  - Resets service state

#### `scripts/get_supabase_connection.py` - Connection Info
- **Purpose**: Get connection information for debugging
- **Usage**: `python scripts/get_supabase_connection.py`
- **Provides**:
  - Connection strings
  - Service URLs
  - Configuration details

### Maintenance Scripts (`scripts/maintenance/`)

#### `scripts/maintenance/backup.py` - Database Backup
- **Purpose**: Create database backups
- **Usage**: `python scripts/maintenance/backup.py`
- **Features**:
  - Automated backups
  - Compression
  - Retention management

#### `scripts/maintenance/monitor.py` - System Monitoring
- **Purpose**: Monitor system health
- **Usage**: `python scripts/maintenance/monitor.py`
- **Monitors**:
  - Service status
  - Resource usage
  - Performance metrics

### Migration Scripts (`scripts/migration/`)

#### `scripts/migration/migrate.py` - Database Migrations
- **Purpose**: Run database migrations
- **Usage**: `python scripts/migration/migrate.py`
- **Features**:
  - Schema migrations
  - Data migrations
  - Rollback support

## 🔧 Setup Sequence

The correct sequence for setting up the project is:

1. **Prerequisites** → `scripts/setup_prerequisites.sh`
2. **Environment** → `setup.sh` or `scripts/setup_master.py`
3. **Database** → `scripts/setup/db_setup.py`
4. **Extensions** → `scripts/setup/extensions/01_extensions.sql`
5. **Security** → `scripts/setup/security.py`
6. **Verification** → `scripts/test_setup.py`

## 🚨 Troubleshooting

### Common Issues and Solutions

#### Port Conflicts
```bash
# Check what's using the ports
lsof -i :54323  # Database
lsof -i :3000   # API
lsof -i :3001   # Studio

# Kill conflicting processes
kill -9 <PID>
```

#### Docker Issues
```bash
# Restart Docker
sudo systemctl restart docker

# Clean up Docker
docker system prune -a

# Reset containers
docker-compose down -v
docker-compose up -d
```

#### Database Issues
```bash
# Check database logs
docker-compose logs supabase-db

# Restart database
docker-compose restart supabase-db

# Reset database
docker-compose down -v
docker-compose up -d supabase-db
```

#### Permission Issues
```bash
# Fix script permissions
chmod +x setup.sh
chmod +x scripts/*.py
chmod +x scripts/setup/*.py

# Fix Docker permissions (Linux)
sudo chmod 666 /var/run/docker.sock
```

## 📊 Script Dependencies

```
setup.sh
├── docker-compose.yml
├── requirements.txt
└── scripts/test_setup.py

scripts/setup_master.py
├── docker-compose.yml
├── requirements.txt
└── scripts/test_setup.py

scripts/setup/db_setup.py
├── schema.sql
├── scripts/setup/extensions/
└── supabase/seed.sql

scripts/test_setup.py
├── docker-compose.yml
└── All services running
```

## 🎯 Best Practices

1. **Always run from project root**: All scripts assume they're run from the project root directory
2. **Check prerequisites first**: Use `scripts/setup_master.py --check-only` to verify prerequisites
3. **Use virtual environment**: Always activate the Python virtual environment before running scripts
4. **Read error messages**: Most scripts provide detailed error information
5. **Check logs**: Use `docker-compose logs [service-name]` for service-specific issues
6. **Backup before changes**: Use `scripts/maintenance/backup.py` before making schema changes

## 📞 Getting Help

If you encounter issues:

1. **Check the logs**: `docker-compose logs [service-name]`
2. **Run tests**: `python scripts/test_setup.py`
3. **Check prerequisites**: `python scripts/setup_master.py --check-only`
4. **Read documentation**: Check `JUNIOR_DEV_SETUP.md` for detailed setup instructions
5. **Reset everything**: `docker-compose down -v && docker-compose up -d`

## 🔄 Development Workflow

1. **Setup**: Use `setup.sh` for initial setup
2. **Development**: Make changes in the `apps/` directory
3. **Testing**: Use `scripts/test_setup.py` to verify changes
4. **Maintenance**: Use scripts in `scripts/maintenance/` for ongoing tasks
5. **Migrations**: Use scripts in `scripts/migration/` for database changes 