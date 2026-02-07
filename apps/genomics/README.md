# Genomics Service

## Overview

The Genomics Service is a comprehensive microservice for genomic analysis and genetic counseling within the Personal Health Assistant platform. It provides advanced capabilities for DNA sequence analysis, genetic variant detection, pharmacogenomics, ancestry analysis, and genetic counseling support.

## Key Features

### 🧬 **Genomic Data Management**
- Upload and storage of genomic data files (FASTQ, BAM, VCF, etc.)
- Quality assessment and validation
- Data processing and analysis workflows
- Secure file storage and access control

### 🔍 **Genetic Variant Analysis**
- Detection and annotation of genetic variants
- Clinical significance assessment
- Population frequency analysis
- Variant filtering and search capabilities

### 💊 **Pharmacogenomics**
- Drug-gene interaction analysis
- Metabolizer status assessment
- Personalized medication recommendations
- Drug response predictions

### 🌍 **Ancestry Analysis**
- Ancestry composition analysis
- Geographic origins mapping
- Haplogroup analysis
- Population matching and migration patterns

### 🧬 **Genetic Counseling**
- Counseling session management
- Risk assessment and reporting
- Educational materials and resources
- Follow-up scheduling and tracking

## Architecture

### Technology Stack
- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **File Storage**: Local filesystem with checksum validation
- **Authentication**: JWT-based with role-based access control
- **Containerization**: Docker with multi-stage builds
- **API Documentation**: OpenAPI/Swagger

### Service Structure
```
apps/genomics/
├── api/                    # API endpoints
│   ├── genomic_data.py    # Data management endpoints
│   ├── analysis.py        # Analysis workflow endpoints
│   ├── variants.py        # Variant management endpoints
│   ├── pharmacogenomics.py # Drug-gene interaction endpoints
│   ├── ancestry.py        # Ancestry analysis endpoints
│   └── counseling.py      # Genetic counseling endpoints
├── models/                 # Data models
│   ├── genomic_data.py    # Genomic data and variants
│   ├── analysis.py        # Analysis results
│   └── counseling.py      # Counseling sessions and reports
├── services/              # Business logic
│   ├── genomic_data_service.py
│   ├── analysis_service.py
│   ├── variant_service.py
│   ├── pharmacogenomics_service.py
│   ├── ancestry_service.py
│   └── counseling_service.py
├── agents/                # AI agents (future)
├── main.py               # FastAPI application
├── requirements.txt      # Python dependencies
├── Dockerfile           # Container configuration
└── create_tables.py     # Database setup
```

## API Endpoints

### Genomic Data Management
- `POST /api/v1/genomic-data/` - Create genomic data record
- `GET /api/v1/genomic-data/` - List user's genomic data
- `GET /api/v1/genomic-data/{id}` - Get specific genomic data
- `PUT /api/v1/genomic-data/{id}` - Update genomic data
- `DELETE /api/v1/genomic-data/{id}` - Delete genomic data
- `POST /api/v1/genomic-data/upload` - Upload genomic file
- `GET /api/v1/genomic-data/{id}/download` - Download genomic file
- `POST /api/v1/genomic-data/{id}/process` - Process genomic data
- `GET /api/v1/genomic-data/{id}/quality` - Get quality metrics
- `POST /api/v1/genomic-data/{id}/validate` - Validate genomic data

### Analysis Workflows
- `POST /api/v1/analysis/` - Create and start analysis
- `GET /api/v1/analysis/` - List analyses
- `GET /api/v1/analysis/{id}` - Get analysis details
- `GET /api/v1/analysis/{id}/status` - Get analysis status
- `GET /api/v1/analysis/{id}/results` - Get analysis results
- `POST /api/v1/analysis/{id}/cancel` - Cancel analysis

### Genetic Variants
- `POST /api/v1/variants/` - Create variant record
- `GET /api/v1/variants/` - List variants
- `GET /api/v1/variants/search` - Search variants
- `GET /api/v1/variants/chromosome/{chr}` - Get variants by chromosome
- `GET /api/v1/variants/gene/{gene}` - Get variants by gene
- `GET /api/v1/variants/rs/{rs_id}` - Get variants by rs ID
- `POST /api/v1/variants/{id}/annotate` - Annotate variant

### Pharmacogenomics
- `POST /api/v1/pharmacogenomics/profiles` - Create profile
- `GET /api/v1/pharmacogenomics/profiles` - List profiles
- `GET /api/v1/pharmacogenomics/drug-interactions` - Get drug interactions
- `GET /api/v1/pharmacogenomics/metabolizer-status` - Get metabolizer status
- `POST /api/v1/pharmacogenomics/drug-response` - Predict drug response
- `GET /api/v1/pharmacogenomics/medication-recommendations` - Get recommendations

### Ancestry Analysis
- `POST /api/v1/ancestry/` - Create ancestry analysis
- `GET /api/v1/ancestry/` - List ancestry analyses
- `GET /api/v1/ancestry/composition` - Get ancestry composition
- `GET /api/v1/ancestry/geographic-origins` - Get geographic origins
- `GET /api/v1/ancestry/haplogroups` - Get haplogroups
- `GET /api/v1/ancestry/population-matches` - Get population matches

### Genetic Counseling
- `POST /api/v1/counseling/` - Create counseling session
- `GET /api/v1/counseling/` - List counseling sessions
- `POST /api/v1/counseling/risk-reports` - Create risk report
- `GET /api/v1/counseling/risk-reports` - List risk reports
- `GET /api/v1/counseling/educational-materials` - Get educational materials
- `GET /api/v1/counseling/recommendations` - Get recommendations

## Data Models

### Core Entities

#### GenomicData
- User association and file metadata
- Quality metrics and processing status
- Data source and format information

#### GeneticVariant
- Chromosome, position, and allele information
- Clinical significance and annotations
- Population frequency data

#### PharmacogenomicProfile
- Drug-gene interaction data
- Metabolizer status information
- Medication recommendations

#### GenomicAnalysis
- Analysis type and status tracking
- Results storage and confidence scores
- Processing metadata

#### DiseaseRiskAssessment
- Disease-specific risk calculations
- Contributing genetic factors
- Clinical recommendations

#### AncestryAnalysis
- Ancestry composition percentages
- Geographic origins and haplogroups
- Population matching data

#### GeneticCounseling
- Session scheduling and management
- Patient information and concerns
- Follow-up tracking

## Security & Privacy

### Data Protection
- **HIPAA Compliance**: All genomic data is handled according to HIPAA guidelines
- **Encryption**: Data encrypted at rest and in transit
- **Access Control**: Role-based access with user-specific data isolation
- **Audit Logging**: Comprehensive audit trails for all data access

### Privacy Features
- **Data Anonymization**: Optional data anonymization for research
- **Consent Management**: Explicit consent tracking for data usage
- **Data Retention**: Configurable data retention policies
- **Right to Deletion**: Full data deletion capabilities

## Deployment

### Prerequisites
- PostgreSQL 15+
- Redis 7+
- Python 3.11+
- Docker & Docker Compose

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/genomics_db

# Redis
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET_KEY=your-secret-key
CORS_ORIGINS=["http://localhost:3000"]

# Service URLs
AUTH_SERVICE_URL=http://auth-service:8000
USER_PROFILE_SERVICE_URL=http://user-profile-service:8001
MEDICAL_RECORDS_SERVICE_URL=http://medical-records-service:8002

# Genomics-specific
GENOMIC_DATA_PATH=/app/genomic_data
MAX_FILE_SIZE=1073741824  # 1GB
ALLOWED_FILE_TYPES=fastq,bam,vcf,gff,bed,json,csv,txt
```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d genomics-service

# Or build individually
docker build -t genomics-service .
docker run -p 8012:8012 genomics-service
```

### Database Setup
```bash
# Create tables and indexes
python apps/genomics/create_tables.py

# Or run migrations
alembic upgrade head
```

## Monitoring & Health Checks

### Health Endpoints
- `GET /health` - Service health status
- `GET /ready` - Service readiness check
- `GET /metrics` - Prometheus metrics

### Monitoring
- **Application Metrics**: Request rates, response times, error rates
- **Database Metrics**: Connection pool, query performance
- **File Storage**: Disk usage, file operations
- **Analysis Metrics**: Processing times, success rates

## Development

### Local Development Setup
```bash
# Clone repository
git clone <repository-url>
cd PersonalHealthAssistant

# Install dependencies
pip install -r apps/genomics/requirements.txt

# Set up environment
export DATABASE_URL=postgresql://user:password@localhost:5432/genomics_db
export REDIS_URL=redis://localhost:6379

# Run database setup
python apps/genomics/create_tables.py

# Start service
uvicorn apps.genomics.main:app --host 0.0.0.0 --port 8012 --reload
```

### Testing
```bash
# Run unit tests
pytest apps/genomics/tests/unit/

# Run integration tests
pytest apps/genomics/tests/integration/

# Run with coverage
pytest --cov=apps.genomics --cov-report=html
```

### Code Quality
```bash
# Format code
black apps/genomics/

# Lint code
flake8 apps/genomics/

# Type checking
mypy apps/genomics/

# Security scan
bandit -r apps/genomics/
```

## Integration

### Service Dependencies
- **Auth Service**: User authentication and authorization
- **User Profile Service**: User profile information
- **Medical Records Service**: Medical history integration
- **Knowledge Graph Service**: Medical knowledge and ontologies

### External Integrations
- **dbSNP**: Variant annotation and frequency data
- **ClinVar**: Clinical significance information
- **PharmGKB**: Pharmacogenomic knowledge
- **1000 Genomes**: Population frequency data

## Future Enhancements

### Planned Features
- **AI-Powered Analysis**: Machine learning for variant interpretation
- **Real-time Processing**: Stream processing for large datasets
- **Advanced Visualization**: Interactive genomic data visualization
- **Mobile Support**: Mobile-optimized API endpoints
- **Batch Processing**: Large-scale batch analysis capabilities

### Research Integration
- **Research Portal**: Secure data sharing for research
- **Clinical Trials**: Integration with clinical trial matching
- **Drug Discovery**: Support for drug discovery workflows
- **Population Studies**: Large-scale population genomics

## Support & Documentation

### API Documentation
- **Swagger UI**: Available at `/docs` when not in production
- **ReDoc**: Available at `/redoc`
- **OpenAPI Spec**: Available at `/openapi.json`

### Contact
- **Technical Support**: tech-support@personalhealthassistant.com
- **Documentation**: docs.personalhealthassistant.com
- **GitHub Issues**: github.com/personalhealthassistant/issues

## License

This service is part of the Personal Health Assistant platform and is licensed under the MIT License. See LICENSE file for details. 