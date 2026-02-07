# Personal Health Assistant

A comprehensive health management platform with AI-powered insights, real-time monitoring, and personalized recommendations.

**How to use:**
1. Run `./setup.sh` from the project root.  
   - This will check prerequisites, set up the Python environment, install all missing dependencies, start Docker services, set up the database, run tests, and validate everything.
2. If you want to install only missing dependencies, run:  
   `python scripts/install_missing_dependencies.py`
3. To check your environment at any time, run:  
   `python scripts/validate_requirements.py`

**You are now ready for development!**  
All tools, frameworks, and software are in place and validated.  
If you add new dependencies in the future, just update `requirements.txt` and rerun the setup or installer script.

Let me know if you want to further customize the setup or need onboarding instructions for new developers!


## 🚀 Quick Start for New Developers

### One-Command Setup (Recommended)
```bash
git clone <repository-url>
cd PersonalHealthAssistant
./setup.sh
```

### Alternative Setup Options
- **Python Script**: `python scripts/setup_master.py`
- **Manual Setup**: See [JUNIOR_DEV_SETUP.md](JUNIOR_DEV_SETUP.md)
- **Detailed Guide**: See [scripts/README.md](scripts/README.md)

## 📋 Prerequisites

- Docker & Docker Compose
- Python 3.9+
- Git

## 🏗️ Architecture

### Core Infrastructure
- **Database Connection Management** - Connection pooling, health monitoring, async support
- **Logging Infrastructure** - Structured logging with multiple handlers and request tracking
- **Base Service Classes** - Generic CRUD operations with error handling and pagination
- **Authentication Middleware** - JWT-based auth with role-based access control
- **Error Handling Middleware** - Centralized error handling and consistent responses

### Core Services
- **Database**: PostgreSQL with TimescaleDB for time-series data
- **API**: PostgREST for RESTful database access
- **Vector DB**: Qdrant for AI/ML features
- **Message Queue**: Kafka for real-time processing
- **Studio**: Supabase Studio for database management

### Application Modules
- **AI Insights**: Machine learning and analytics
- **Health Tracking**: Vital signs, activity, sleep monitoring
- **Medical Records**: Image processing, lab results, reports
- **Authentication**: User management and security
- **E-commerce**: Product catalog and ordering
- **Genomics**: Genetic data analysis
- **Voice Input**: Speech-to-text processing

## 🔧 Development

### Services Overview
- **Database**: `localhost:54323`
- **REST API**: `localhost:3000`
- **Studio**: `localhost:3001`
- **Vector DB**: `localhost:6333`
- **Message Queue**: `localhost:9092`

### Quick Commands
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs [service-name]

# Run tests
python scripts/test_setup.py

# Stop all services
docker-compose down
```

## 📚 Documentation

- **[Junior Developer Setup](JUNIOR_DEV_SETUP.md)** - Complete setup guide for new developers
- **[Core Infrastructure](docs/CORE_INFRASTRUCTURE.md)** - Detailed documentation of core components
- **[Core Infrastructure Quick Reference](docs/CORE_INFRASTRUCTURE_QUICK_REFERENCE.md)** - Quick reference guide
- **[Scripts Documentation](scripts/README.md)** - Detailed guide for all setup and maintenance scripts
- **[API Documentation](http://localhost:3000)** - Interactive API docs (when running)
- **[Database Studio](http://localhost:3001)** - Database management interface (when running)

## 🛠️ Setup Scripts

### Automated Setup
- `setup.sh` - One-command complete setup
- `scripts/setup_master.py` - Python-based setup with detailed logging

### Manual Setup
- `scripts/setup_prerequisites.sh` - Install system dependencies
- `scripts/setup/db_setup.py` - Database initialization
- `scripts/test_setup.py` - Comprehensive testing

### Troubleshooting
- `scripts/fix_supabase_connection.py` - Fix connection issues
- `scripts/wake_up_supabase.py` - Service recovery
- `scripts/maintenance/` - Backup and monitoring tools

## 🧪 Testing

```bash
# Run comprehensive tests
python scripts/test_setup.py

# Test specific components
python scripts/setup/check_extensions.py
```

## 🚨 Troubleshooting

### Common Issues
1. **Port Conflicts**: Check `lsof -i :[port]` and kill conflicting processes
2. **Docker Issues**: Restart Docker and run `docker system prune -a`
3. **Database Issues**: Check logs with `docker-compose logs supabase-db`
4. **Permission Issues**: Run `chmod +x setup.sh` and fix Docker permissions

### Reset Everything
```bash
docker-compose down -v
docker-compose up -d --build
```

## 📊 Database Schema

The database includes 45+ tables covering:
- User management and authentication
- Health metrics and vital signs
- Medical records and imaging
- Device integration and activity tracking
- AI/ML features and analytics
- E-commerce and inventory
- Genomics and personalized medicine

## 🔐 Security

- Row Level Security (RLS) policies protect user data
- All services run locally for development
- Strong passwords and encryption
- Audit logging for compliance

## 🤝 Contributing

1. Follow the setup guide in `JUNIOR_DEV_SETUP.md`
2. Make changes in the `apps/` directory
3. Test with `python scripts/test_setup.py`
4. Follow the project's coding standards
5. Submit pull requests with clear descriptions

## 📞 Support

- **Setup Issues**: Check `JUNIOR_DEV_SETUP.md` and `scripts/README.md`
- **Service Logs**: `docker-compose logs [service-name]`
- **API Issues**: Check `http://localhost:3000` for documentation
- **Database Issues**: Use `http://localhost:3001` for management

## 📄 License

[Add your license information here]

---

**Ready to start?** Run `./setup.sh` and begin developing!
