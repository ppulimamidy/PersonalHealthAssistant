# Personal Physician Assistant (PPA) - Data Model

## Overview
This repository contains the comprehensive data model for the Personal Physician Assistant (PPA) application, built on Supabase. The schema is designed to support a wide range of healthcare and wellness features while maintaining strict data privacy and security standards.

## Key Features

### 1. Authentication & User Management
- Secure user authentication via Supabase Auth
- Role-based access control (Patient, Doctor, Admin)
- User profile management with health-specific attributes

### 2. Medical Records & Health Data
- Comprehensive medical history tracking
- Medication and supplement management
- Lab results and biomarker tracking
- Genomic data integration
- Voice and multimodal input support
- Real-time health data streaming
- Hybrid event processing
- Detailed food tracking and nutrition analysis
- Enhanced exercise and activity monitoring
- Comprehensive prescription management
- Detailed lab test definitions and panels

### 3. Healthcare Provider Integration
- Provider profiles and credentials
- Appointment scheduling
- Secure messaging system
- Document sharing capabilities

### 4. E-commerce & Supplement Management
- Product catalog with health-specific attributes
- Order management
- Subscription handling
- Photo-based supplement verification

### 5. AI & Analytics
- Medical literature integration
- Knowledge graph for medical terms and interactions
- Causal inference tracking
- Anomaly detection
- Analytics snapshots
- Model training and versioning
- Semantic search capabilities
- Hybrid vector search with pgvector and Qdrant

### 6. Privacy & Compliance
- Audit logging
- Consent management
- Data access tracking
- HIPAA compliance features
- Version control for critical documents

## Schema Components

### Core Tables
- `users`: Extended user profiles with health-specific attributes
- `medical_records`: Comprehensive medical history
- `medications`: Medication tracking with interactions
- `supplements`: Supplement management with verification
- `healthcare_providers`: Provider profiles and credentials
- `appointments`: Appointment scheduling and management
- `food_items`: Detailed food database with nutritional information
- `nutrition_log_items`: Granular food tracking and logging
- `activity_types`: Exercise and activity definitions
- `activity_routes`: GPS and route tracking for activities
- `activity_metrics`: Detailed exercise metrics
- `prescriptions`: Comprehensive prescription management
- `lab_tests`: Standardized lab test definitions
- `lab_test_panels`: Common test panel configurations

### Medical Knowledge & AI
- `medical_literature`: Medical research and clinical data
- `medical_terms`: Standardized medical terminology
- `interaction_graph`: Drug, supplement, and condition interactions
- `causal_inferences`: AI-driven cause-effect relationships
- `event_logs`: System event tracking for AI analysis
- `training_datasets`: AI model training data
- `model_versions`: AI model versioning
- `model_predictions`: Model inference results

### Lab & Biomarker Data
- `lab_results`: Laboratory test results
- `biomarkers`: Individual biomarker measurements
- `genomic_markers`: Genetic marker definitions
- `user_genomics`: User-specific genomic data

### Multimodal Input
- `voice_logs`: Voice input processing
- `raw_input_data`: Various input type handling
- `supplement_photos`: Image-based supplement verification

### Analytics & Monitoring
- `analytics_snapshots`: User health metrics
- `anomaly_alerts`: Health anomaly detection
- `event_timelines`: Chronological health events
- `report_templates`: Standardized reporting

### Privacy & Compliance
- `audit_logs`: System access and changes
- `consent_records`: User consent management
- `clinician_annotations`: Provider notes and observations

### Enhanced Reporting
- `daily_health_summaries`: Daily health metrics and insights
- `monthly_wellness_reports`: Monthly health trends and recommendations
- `report_templates`: Customizable report templates
- `user_feedback`: User feedback on recommendations and insights

### Consent & Privacy
- `consent_types`: Granular consent categories
- `consent_records`: User consent tracking
- `audit_logs`: Comprehensive audit trail
- `clinician_annotations`: Provider notes and observations

## Performance Optimizations

### OLAP Analytics & Dashboarding
- DuckDB integration for high-performance analytics:
  - Daily health metrics aggregation
  - Weekly health trends analysis
  - Monthly health insights generation
  - Efficient querying of large datasets
- Analytics schema with optimized views:
  - Materialized views for common queries
  - Foreign tables for DuckDB integration
  - Dashboard-ready metrics
  - Automated data refresh

### Analytics Features
- Comprehensive health metrics:
  - Vital signs trends
  - Activity and sleep patterns
  - Nutrition analysis
  - Supplement and medication tracking
  - Anomaly detection
- Advanced analytics:
  - Health scoring system
  - Risk factor analysis
  - Improvement tracking
  - Compliance monitoring
  - Wellness metrics

### Data Warehouse Integration
- DuckDB for BI queries:
  - Columnar storage for analytics
  - Efficient aggregation
  - Fast query performance
  - Parquet format support
- ETL Process:
  - Daily data refresh
  - Automated aggregation
  - Incremental updates
  - Data validation

### Time-Series Data Management
- TimescaleDB integration for efficient time-series data handling
- Hybrid streaming architecture:
  - Kafka for high-frequency data ingestion
  - Stream buffer for data queuing
  - Batch processing for efficiency
  - Error handling and retry logic
- Data retention policies with tiered storage:
  - Recent data (detailed):
    - Device data: 1 year
    - Event logs: 6 months
    - Voice logs: 3 months
    - Vital signs: 1 year
  - Historical data (aggregated):
    - Device data: 5 years
    - Event logs: 2 years
    - Voice logs: 1 year
    - Vital signs: 5 years

### Time-Series Optimizations
- Hypertables for efficient partitioning:
  - Daily chunks for high-resolution data
  - Automatic chunk management
  - Efficient query performance
- Continuous aggregates:
  - Hourly aggregations for device data
  - Hourly aggregations for vital signs
  - Automatic refresh policies
- Automated data management:
  - Daily cleanup of old data
  - Automatic migration to aggregated tables
  - Retention policy enforcement

### AI & Search Optimizations
- Vector indexes for semantic search:
  - IVFFlat indexes on embedding columns
  - Optimized for cosine similarity search
  - Hybrid search architecture:
    - pgvector for small collections (<10M vectors)
    - Qdrant for large-scale collections (100M+ vectors)
    - Automatic collection size detection
    - Seamless query routing
- Efficient model prediction tracking
- Version control for AI models and datasets

### Version Control
- Support for document versioning:
  - `report_templates`
  - `consent_records`
  - `medical_literature`
- Tracks changes and maintains history

## Security Features
- Row Level Security (RLS) policies
- Encrypted sensitive data
- Audit logging
- Consent management
- Role-based access control

## Data Privacy
- HIPAA compliance measures
- Data encryption
- Access control
- Audit trails
- Consent management

## Getting Started

### Prerequisites
- Supabase account
- PostgreSQL 12+
- Node.js 14+
- pgvector extension
- TimescaleDB extension
- pg_cron extension
- DuckDB extension
- DuckDB Foreign Data Wrapper
- Qdrant vector database
- http extension for Qdrant API calls
- Kafka cluster
- pg_kafka extension

### Installation
1. Clone the repository
2. Set up Supabase project
3. Enable required extensions:
   ```sql
   CREATE EXTENSION IF NOT EXISTS "timescaledb";
   CREATE EXTENSION IF NOT EXISTS "pgvector";
   CREATE EXTENSION IF NOT EXISTS "pg_cron";
   CREATE EXTENSION IF NOT EXISTS "duckdb_fdw";
   CREATE EXTENSION IF NOT EXISTS "pg_kafka";
   ```
4. Configure DuckDB:
   ```sql
   CREATE SERVER duckdb_server
   FOREIGN DATA WRAPPER duckdb_fdw
   OPTIONS (database '/path/to/analytics.duckdb');
   ```
5. Run the schema.sql file
6. Configure environment variables
7. Initialize the application

### Environment Variables
```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key
KAFKA_BROKERS=your_kafka_brokers
KAFKA_TOPIC=your_kafka_topic
```

### Analytics Configuration
The system implements a comprehensive analytics solution:

1. **Data Aggregation**
   - Daily metrics calculation
   - Weekly trend analysis
   - Monthly insight generation
   - Automated data refresh

2. **Performance Optimization**
   - Materialized views for common queries
   - Efficient indexing strategy
   - Partitioned data storage
   - Optimized query patterns

3. **Dashboard Integration**
   - Pre-calculated metrics
   - Real-time data updates
   - Historical trend analysis
   - Customizable views

4. **Data Refresh**
   - Daily automated updates
   - Incremental processing
   - Data validation
   - Error handling

### Data Retention Configuration
The system implements a tiered data retention strategy:

1. **Recent Data (Detailed)**
   - Full resolution data for recent time periods
   - Optimized for real-time queries and analysis
   - Automatically partitioned by day

2. **Historical Data (Aggregated)**
   - Daily aggregations for older data
   - Maintains statistical summaries
   - Optimized for long-term trend analysis

3. **Data Migration**
   - Automatic daily migration of old data to aggregated tables
   - Preserves important statistics while reducing storage
   - Maintains data accessibility for historical analysis

### Maintenance
- Daily automated cleanup of old data
- Automatic aggregation of historical data
- Continuous aggregate refresh
- Index maintenance
- Storage optimization

### Vector Search Configuration
The system implements a hybrid vector search architecture:

1. **Collection Management**
   - Automatic collection size detection
   - Dynamic routing between pgvector and Qdrant
   - Collection-specific configuration
   - Metadata and payload support

2. **Search Capabilities**
   - Cosine similarity search
   - Configurable distance metrics
   - Threshold-based filtering
   - Payload-based filtering
   - Batch search support

3. **Performance Optimization**
   - Local caching for small collections
   - Distributed search for large collections
   - Automatic vector synchronization
   - Efficient index management

4. **Data Synchronization**
   - Automatic vector sync to Qdrant
   - Incremental updates
   - Error handling and retry logic
   - Consistency checks

### Stream Processing Configuration
The system implements a hybrid streaming architecture:

1. **Data Ingestion**
   - Kafka for high-frequency data
   - Stream buffer for data queuing
   - Batch processing for efficiency
   - Error handling and retry logic

2. **Processing Pipeline**
   - Configurable batch sizes
   - Stream type-specific processing
   - Error tracking and monitoring
   - Automatic cleanup

3. **Performance Optimization**
   - Partitioned buffer tables
   - Efficient indexing
   - Batch processing
   - Automatic cleanup

4. **Monitoring & Maintenance**
   - Processing status tracking
   - Error logging and analysis
   - Performance monitoring
   - Automatic cleanup

## API Endpoints

### Analytics Endpoints
- GET /analytics/daily-metrics
- GET /analytics/weekly-trends
- GET /analytics/monthly-insights
- GET /analytics/health-summary
- GET /analytics/dashboard-metrics

## Contributing
Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License
This project is licensed under the MIT License - see the LICENSE.md file for details.

## Support
For support, please open an issue in the GitHub repository or contact the development team.

## Acknowledgments
- Supabase team for the excellent platform
- Healthcare professionals who provided domain expertise
- Open source community for various tools and libraries

### Data Management
- Tiered storage strategy
- Automated cleanup
- Data aggregation
- Backup and recovery
- Status tracking for all entities
- Comprehensive error handling

### Enhanced Features
1. **Food Tracking**
   - Detailed nutritional information
   - Barcode scanning support
   - Serving size management
   - Allergen tracking
   - Ingredient lists

2. **Exercise Monitoring**
   - GPS route tracking
   - Elevation data
   - Sport-specific metrics
   - Intensity tracking
   - Custom metrics support

3. **Prescription Management**
   - Refill tracking
   - Pharmacy integration
   - Provider linking
   - Status monitoring
   - Prescription history

4. **Lab Test Management**
   - Standardized test definitions
   - LOINC code integration
   - Test panel support
   - Reference ranges
   - Preparation instructions

5. **Health Reporting**
   - Daily summaries
   - Monthly wellness reports
   - Customizable templates
   - Trend analysis
   - Achievement tracking

6. **User Feedback**
   - Recommendation feedback
   - Insight ratings
   - Report feedback
   - Improvement tracking
   - User satisfaction metrics

7. **Consent Management**
   - Granular consent types
   - Data category tracking
   - Retention periods
   - Required consents
   - Consent history 