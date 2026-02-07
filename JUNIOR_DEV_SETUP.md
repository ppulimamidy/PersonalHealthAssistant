# 🚦 First-Day Onboarding Checklist for New Developers

Welcome to the Personal Health Assistant project! Follow this checklist to get set up and ready to develop on your first day.

## ✅ First-Day Developer Checklist

- [ ] **1. Clone the repository**
    - `git clone <repository-url>`
    - `cd PersonalHealthAssistant`

- [ ] **2. Review the project structure**
    - Skim the `README.md` for a high-level overview
    - Open `JUNIOR_DEV_SETUP.md` (this file) for step-by-step setup

- [ ] **3. Install prerequisites**
    - Docker & Docker Compose
    - Python 3.9+
    - Git
    - (Optional) Make
    - See the "Prerequisites" section below for install commands

- [ ] **4. Set up your environment variables**
    - Copy `.env.example` to `.env`
    - Fill in any required values (see `README.md` for details)

- [ ] **5. Run the one-command setup**
    - `chmod +x setup.sh`
    - `./setup.sh`
    - (Or use `python scripts/setup_master.py` for detailed output)

- [ ] **6. Verify your setup**
    - All Docker services should be running: `docker-compose ps`
    - API should be live: [http://localhost:3000](http://localhost:3000)
    - Database Studio: [http://localhost:3001](http://localhost:3001)
    - Run tests: `python scripts/test_setup.py`

- [ ] **7. Explore the codebase**
    - Browse the `apps/` directory for application modules
    - Review `schema.sql` for the database structure
    - Check `scripts/README.md` for script explanations

- [ ] **8. Read the development workflow**
    - See the "Development Workflow" section below
    - Understand how to make, test, and commit changes

- [ ] **9. Ask for help if needed**
    - Check the troubleshooting sections in this file and `scripts/README.md`
    - Use `docker-compose logs [service-name]` for service logs
    - Reach out to your onboarding mentor or team lead

- [ ] **10. Start your first task!**
    - Pick a starter issue or feature from the team
    - Set up your dev branch and begin coding 🚀

---

# Personal Health Assistant - Junior Developer Setup Guide

This guide will help you set up the complete development environment for the Personal Health Assistant project from scratch.

## 🚀 Quick Start (5 minutes)

If you want to get up and running quickly:

```bash
# 1. Clone the repository
git clone <repository-url>
cd PersonalHealthAssistant

# 2. Run the automated setup
chmod +x scripts/setup_prerequisites.sh
./scripts/setup_prerequisites.sh

# 3. Start the development environment
docker-compose up -d

# 4. Verify everything is working
python scripts/test_setup.py
```

## 📋 Prerequisites

Before starting, ensure you have the following installed:

- **Docker & Docker Compose** (latest version)
- **Python 3.9+**
- **Git**
- **Make** (optional, for using Makefile commands)

### Installing Prerequisites

#### macOS (using Homebrew):
```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install prerequisites
brew install docker docker-compose python@3.9 git make
```

#### Ubuntu/Debian:
```bash
# Update package list
sudo apt update

# Install prerequisites
sudo apt install -y docker.io docker-compose python3 python3-pip git make

# Add user to docker group
sudo usermod -aG docker $USER
```

#### Windows:
- Install [Docker Desktop](https://www.docker.com/products/docker-desktop)
- Install [Python](https://www.python.org/downloads/)
- Install [Git](https://git-scm.com/download/win)

## 🛠️ Detailed Setup Process

### Step 1: Clone and Navigate to Project

```bash
git clone <repository-url>
cd PersonalHealthAssistant
```

### Step 2: Set Up Python Environment

**Option A: Automated Setup (Recommended)**
```bash
# Run the one-command setup (includes virtual environment setup)
chmod +x setup.sh
./setup.sh
```

**Option B: Manual Setup**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# .\venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

**Option C: Dedicated Virtual Environment Script**
```bash
# Create and set up virtual environment with validation
python scripts/setup_venv.py

# Or use specific commands:
python scripts/setup_venv.py create    # Create venv only
python scripts/setup_venv.py validate  # Check venv status
python scripts/setup_venv.py install   # Install requirements only
```

**Virtual Environment Validation:**
```bash
# Check if virtual environment is active
python scripts/setup_venv.py validate

# Or use the comprehensive validation
python scripts/validate_requirements.py
```

**Important Notes:**
- The setup script automatically handles virtual environment creation and activation
- Always ensure your virtual environment is active before running Python scripts
- You can tell it's active when you see `(venv)` at the start of your command prompt
- To deactivate: `deactivate`
- To reactivate: `source venv/bin/activate` (macOS/Linux) or `.\venv\Scripts\activate` (Windows)

### Step 3: Start Development Services

```bash
# Start all services (database, API, etc.)
docker-compose up -d

# Wait for services to be ready (about 30 seconds)
sleep 30
```

### Step 4: Verify Setup

```bash
# Run the comprehensive test script
python scripts/test_setup.py
```

## 🔧 What Gets Set Up

### Services Started:
- **PostgreSQL Database** (port 54323) - Main database with TimescaleDB
- **PostgREST API** (port 3000) - REST API for database access
- **Supabase Studio** (port 3001) - Database management interface
- **Qdrant** (ports 6333-6334) - Vector database for AI features
- **Kafka** (port 9092) - Message queue for real-time features
- **Zookeeper** (port 2181) - Required for Kafka

### Database Features:
- 45+ tables for health data management
- Row Level Security (RLS) policies
- Advanced PostgreSQL extensions (TimescaleDB, pg_trgm, etc.)
- Custom functions for health analytics
- Full-text search capabilities
- JSONB support for flexible data storage

## 📊 Database Schema Overview

The database includes tables for:
- **User Management**: profiles, authentication, permissions
- **Health Data**: metrics, vital signs, symptoms, medications
- **Device Integration**: device data, activity tracking, sleep data
- **Medical Records**: images, reports, lab results
- **Analytics**: insights, anomalies, trends
- **E-commerce**: products, orders, inventory
- **AI/ML**: knowledge graphs, medical literature, genomics

## 🧪 Testing Your Setup

### 1. Check Service Status
```bash
docker-compose ps
```

All services should show as "Up" and "healthy".

### 2. Test Database Connection
```bash
# Connect to database
docker exec supabase_db psql -U postgres -d postgres -c "SELECT version();"
```

### 3. Test API Endpoints
```bash
# Test REST API
curl http://localhost:3000/

# Test health endpoint
curl http://localhost:3000/health
```

### 4. Access Supabase Studio
Open your browser and go to: http://localhost:3001

## 🚨 Troubleshooting

### Common Issues:

#### 1. Port Conflicts
If you get port conflicts, check what's using the ports:
```bash
# Check what's using port 54323
lsof -i :54323

# Check what's using port 3000
lsof -i :3000
```

#### 2. Docker Issues
```bash
# Restart Docker
sudo systemctl restart docker

# Clean up Docker
docker system prune -a
```

#### 3. Database Connection Issues
```bash
# Check database logs
docker-compose logs supabase-db

# Restart database
docker-compose restart supabase-db
```

#### 4. Permission Issues
```bash
# Fix Docker permissions (Linux)
sudo chmod 666 /var/run/docker.sock
```

### Reset Everything
If you need to start fresh:
```bash
# Stop all services
docker-compose down

# Remove all data
docker-compose down -v

# Rebuild and start
docker-compose up -d --build
```

## 📁 Project Structure

```
PersonalHealthAssistant/
├── apps/                    # Application modules
│   ├── ai_insights/        # AI and analytics
│   ├── auth/               # Authentication
│   ├── health_tracking/    # Health data management
│   └── ...                 # Other modules
├── scripts/                # Setup and utility scripts
│   ├── setup/             # Database setup scripts
│   ├── maintenance/       # Maintenance scripts
│   └── migration/         # Database migrations
├── docker-compose.yml     # Service definitions
├── schema.sql            # Database schema
├── requirements.txt      # Python dependencies
└── README.md            # Project documentation
```

## 🔐 Security Notes

- All services run locally only
- Database uses strong passwords (defined in docker-compose.yml)
- RLS policies protect user data
- No sensitive data is committed to version control

## 🚀 Next Steps

After successful setup:

1. **Explore the API**: Visit http://localhost:3000 for API documentation
2. **Use Supabase Studio**: Visit http://localhost:3001 for database management
3. **Start Coding**: Begin with the apps in the `apps/` directory
4. **Read Documentation**: Check the main README.md for project overview

## 📞 Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Look at the logs: `docker-compose logs [service-name]`
3. Run the test script: `python scripts/test_setup.py`
4. Check the main project documentation
5. Open an issue in the repository

## 🎯 Development Workflow

1. **Make Changes**: Edit code in the `apps/` directory
2. **Test Locally**: Use the local database and services
3. **Commit Changes**: Follow the project's git workflow
4. **Deploy**: Use the deployment scripts when ready

---

**You're all set! 🎉**

Your development environment is now ready. You can start building features, testing APIs, and contributing to the Personal Health Assistant project. 