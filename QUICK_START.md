# Personal Health Assistant - Quick Start Guide

## 🚀 Get Started in 5 Minutes

This guide will get you up and running with the Personal Health Assistant in the shortest time possible.

## Prerequisites

- **macOS or Linux** (Windows users can use WSL)
- **Docker Desktop** installed and running
- **Python 3.9+** installed
- **Git** installed

## Step 1: Clone and Setup (2 minutes)

```bash
# Clone the repository
git clone <your-repo-url>
cd PersonalHealthAssistant

# Run the automated setup script
chmod +x scripts/setup_prerequisites.sh
./scripts/setup_prerequisites.sh
```

## Step 2: Configure Environment (1 minute)

```bash
# Edit the .env file with your API keys
nano .env

# Add your actual API keys (replace the placeholder values):
# OPENAI_API_KEY=your-actual-openai-key
# ANTHROPIC_API_KEY=your-actual-anthropic-key
# JWT_SECRET_KEY=your-super-secret-jwt-key
```

## Step 3: Start Services (1 minute)

```bash
# Start all services (PostgreSQL, Qdrant, Kafka, DuckDB)
make start

# Wait for services to be ready (about 30 seconds)
sleep 30
```

## Step 4: Initialize Database (30 seconds)

```bash
# Set up database schema and sample data
make db-setup
```

## Step 5: Verify Everything Works (30 seconds)

```bash
# Run comprehensive tests
make test

# Check service health
make health
```

## 🎉 You're Ready!

Your Personal Health Assistant is now running! Here's what you have:

- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Database**: PostgreSQL on localhost:5432
- **Vector Database**: Qdrant on localhost:6333
- **Message Bus**: Kafka on localhost:9092

## Quick Commands

```bash
# Start the application
make start

# Stop all services
make stop

# View logs
make logs

# Run tests
make test

# Format code
make format

# Check health
make health

# Get help
make help
```

## Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Check the database**: Connect to PostgreSQL and explore the schema
3. **Follow the roadmap**: See `IMPLEMENTATION_ROADMAP.md` for detailed development steps
4. **Start developing**: Begin with Phase 1 of the implementation roadmap

## Troubleshooting

### If services don't start:
```bash
# Check if Docker is running
docker info

# Restart services
make stop
make start
```

### If database setup fails:
```bash
# Check database logs
make logs-postgres

# Restart database
docker-compose restart postgres
make db-setup
```

### If tests fail:
```bash
# Check if all services are running
make health

# Reinstall dependencies
pip install -r requirements.txt
```

## What's Included

✅ **Complete Database Schema** - 50+ tables for health data management  
✅ **Authentication System** - JWT-based auth with role-based access  
✅ **Health Tracking** - Vitals, symptoms, goals, and metrics  
✅ **Device Integration** - Wearable and sensor data processing  
✅ **Medical Records** - Lab results, imaging, and reports  
✅ **AI Integration** - OpenAI and Anthropic API support  
✅ **Analytics** - DuckDB for fast analytics  
✅ **Vector Search** - Qdrant for semantic search  
✅ **Message Bus** - Kafka for event-driven architecture  
✅ **API Gateway** - FastAPI with comprehensive documentation  

## Development Workflow

1. **Daily Start**:
   ```bash
   make start
   make test
   ```

2. **Development**:
   ```bash
   # Create feature branch
   git checkout -b feature/your-feature
   
   # Make changes
   # Run tests
   make test
   
   # Commit
   git add .
   git commit -m "feat: add your feature"
   ```

3. **Daily End**:
   ```bash
   make stop
   ```

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Client Apps   │     │   API Gateway   │     │  Microservices  │
│  (Web/Mobile)   │────▶│  (FastAPI)      │────▶│  (Python)       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Analytics     │     │   Message Bus   │     │   Databases     │
│   (DuckDB)      │◀───▶│   (Kafka)       │◀───▶│  (PostgreSQL)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Services Overview

- **Auth Service**: User authentication and authorization
- **User Profile**: Profile and preferences management
- **Health Tracking**: Vitals, symptoms, and goals
- **Device Data**: Wearable and sensor integration
- **Medical Records**: Lab results and medical documents
- **AI Insights**: Health insights and predictions
- **Voice Input**: Speech processing and transcription
- **Analytics**: Health metrics and reporting
- **Knowledge Graph**: Medical knowledge and relationships

## Ready to Build?

You now have a complete foundation for building a comprehensive health platform. The system is designed to be:

- **Scalable**: Microservices architecture
- **Secure**: JWT auth, RLS policies, encryption
- **Fast**: Optimized database, caching, vector search
- **AI-Ready**: OpenAI/Anthropic integration
- **Compliant**: HIPAA-ready data structures
- **Extensible**: Modular design for easy expansion

Start with the implementation roadmap and build your health platform step by step!

---

**Need Help?** Check the `SETUP_GUIDE.md` for detailed setup instructions or `IMPLEMENTATION_ROADMAP.md` for the complete development plan. 