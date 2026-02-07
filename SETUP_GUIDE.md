# Personal Health Assistant - Setup Guide

This guide will help you set up the complete development environment for the Personal Health Assistant project using Supabase.

## Prerequisites

- Docker and Docker Compose
- Python 3.9+
- Git
- Supabase account and project
- Make (optional, for using Makefile commands)

## Setup Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd PersonalHealthAssistant
```

### 2. Set Up Supabase

1. **Create a Supabase Project**
   - Go to [supabase.com](https://supabase.com)
   - Create a new project
   - Note down your project URL and API keys

2. **Configure Environment Variables**
   - Copy `.env.example` to `.env`
   - Update the following variables with your Supabase credentials:
   ```bash
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_ANON_KEY=your_supabase_anon_key
   SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   ```

### 3. Set Up Python Environment

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Start the Development Environment

```bash
# Start supporting services (Qdrant, Kafka)
docker-compose up -d

# Wait for services to be ready (about 30 seconds)
sleep 30
```

### 5. Initialize the Supabase Database

```bash
# Run the database setup script
python scripts/setup/db_setup.py
```

### 6. Run Tests

```bash
# Run the setup test script
python scripts/test_setup.py
```

## Service Details

### Supabase
- **Project URL**: Your Supabase project URL
- **Database**: PostgreSQL (managed by Supabase)
- **Authentication**: Built-in auth system
- **Real-time**: WebSocket subscriptions
- **Storage**: File storage
- **Edge Functions**: Serverless functions

### Qdrant
- HTTP API: http://localhost:6333
- gRPC API: localhost:6334

### Kafka
- Bootstrap Server: localhost:9092
- Zookeeper: localhost:2181

## Development Workflow

1. **Database Changes**
   - Modify schema.sql for table changes
   - Modify rls_policies.sql for security policy changes
   - Run the database setup script to apply changes:
     ```bash
     python scripts/setup/db_setup.py
     ```

2. **Testing Changes**
   - Run the test script to verify all components:
     ```bash
     python scripts/test_setup.py
     ```

3. **Adding New Dependencies**
   - Add to requirements.txt
   - Rebuild the environment:
     ```bash
     pip install -r requirements.txt
     ```

## Troubleshooting

### Common Issues

1. **Supabase Connection Issues**
   - Verify your Supabase URL and API keys in `.env`
   - Check if your Supabase project is active
   - Ensure your IP is not blocked by Supabase

2. **Database Schema Issues**
   - Check Supabase logs in the dashboard
   - Verify RLS policies are correctly applied
   - Ensure you have the correct permissions

3. **Kafka Connection Issues**
   - Ensure Zookeeper is running: `docker-compose ps zookeeper`
   - Check Kafka logs: `docker-compose logs kafka`
   - Verify port 9092 is not in use

4. **Qdrant Issues**
   - Check if the container is running: `docker-compose ps qdrant`
   - Check logs: `docker-compose logs qdrant`
   - Verify ports 6333 and 6334 are not in use

### Reset Environment

To completely reset the environment:

```bash
# Stop all containers
docker-compose down

# Remove volumes
docker-compose down -v

# Rebuild and start
docker-compose up -d

# Re-run database setup
python scripts/setup/db_setup.py
```

## Monitoring

### Supabase Monitoring

```bash
# Check your Supabase dashboard for:
# - Database logs
# - Authentication logs
# - API usage
# - Storage usage
```

### Kafka Monitoring

```bash
# List topics
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Monitor messages
docker-compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic test_topic --from-beginning
```

### Qdrant Monitoring

```bash
# Check collections
curl http://localhost:6333/collections

# Check collection details
curl http://localhost:6333/collections/test_collection
```

## Security Notes

1. **Supabase Security**
   - Use environment variables for sensitive data
   - Never commit API keys to version control
   - Use RLS policies for data access control
   - Enable MFA for your Supabase account

2. **Network Security**
   - Services are exposed to localhost only
   - Use proper firewall rules in production
   - Consider using Docker networks for isolation

3. **Data Security**
   - Supabase provides automatic backups
   - Encrypt sensitive data
   - Follow HIPAA guidelines for production
   - Use Supabase's built-in security features

## Supabase Features

### Authentication
- Built-in user authentication
- Social login providers
- Row Level Security (RLS)
- JWT tokens

### Database
- PostgreSQL with real-time subscriptions
- Automatic backups
- Database logs and monitoring
- Connection pooling

### Storage
- File upload and management
- Image transformations
- CDN integration

### Edge Functions
- Serverless functions
- TypeScript support
- Global deployment

## Next Steps

1. Review the schema and RLS policies
2. Set up your Supabase project
3. Configure environment variables
4. Run the test script to verify the setup
5. Start developing your application

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Supabase documentation
3. Check the logs in Supabase dashboard
4. Open an issue in the repository 