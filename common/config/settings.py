"""
Application Configuration Settings
Manages all environment variables and application settings.
"""

import os
import logging
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings
from pathlib import Path
import secrets

# Setup logging for settings
logger = logging.getLogger(__name__)


class DatabaseSettings(BaseModel):
    """Database configuration settings"""

    url: str = "postgresql://postgres:postgres@localhost:5432/health_assistant"
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False
    timeout: int = 30

    model_config = {"env_prefix": "DATABASE_"}

    def __init__(self, **data):
        # Workaround: directly read environment variables
        if "DATABASE_URL" in os.environ:
            data["url"] = os.environ["DATABASE_URL"]

        super().__init__(**data)
        logger.info(f"DatabaseSettings initialized with URL: {self.url}")
        logger.info(
            f"DatabaseSettings pool_size: {self.pool_size}, max_overflow: {self.max_overflow}"
        )


class AuthSettings(BaseModel):
    """Authentication configuration settings"""

    secret_key: str = "your-super-secret-jwt-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    class Config:
        env_prefix = "JWT_"

    def __init__(self, **data):
        # Workaround: directly read environment variables
        if "JWT_SECRET_KEY" in os.environ:
            data["secret_key"] = os.environ["JWT_SECRET_KEY"]

        super().__init__(**data)


class SupabaseSettings(BaseModel):
    """Supabase configuration settings"""

    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_role_key: Optional[str] = None

    class Config:
        env_prefix = "SUPABASE_"


class Auth0Settings(BaseModel):
    """Auth0 configuration settings"""

    auth0_domain: Optional[str] = None
    auth0_client_id: Optional[str] = None
    auth0_client_secret: Optional[str] = None
    auth0_audience: Optional[str] = None

    class Config:
        env_prefix = "AUTH0_"


class ExternalServicesSettings(BaseModel):
    """External services configuration"""

    qdrant_url: str = "http://localhost:6333"
    kafka_bootstrap_servers: str = "localhost:9092"
    redis_url: str = "redis://localhost:6379"

    class Config:
        env_prefix = ""

    def __init__(self, **data):
        # Workaround: directly read environment variables
        if "REDIS_URL" in os.environ:
            data["redis_url"] = os.environ["REDIS_URL"]

        super().__init__(**data)


class AISettings(BaseModel):
    """AI/ML services configuration"""

    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    ai_model_name: str = "gpt-4"
    max_tokens: int = 1000
    temperature: float = 0.7

    class Config:
        env_prefix = ""


class StorageSettings(BaseModel):
    """File storage configuration"""

    bucket: str = "health-assistant-storage"
    region: str = "us-east-1"
    access_key: Optional[str] = None
    secret_key: Optional[str] = None

    class Config:
        env_prefix = "STORAGE_"


class MonitoringSettings(BaseModel):
    """Monitoring and observability settings"""

    enable_tracing: bool = True
    enable_metrics: bool = True
    enable_logging: bool = True

    # OpenTelemetry settings
    trace_sampling_rate: float = 0.1  # 10% sampling
    jaeger_host: str = "localhost"
    jaeger_port: int = 6831
    prometheus_port: int = 9090

    # Logging settings
    log_level: str = "INFO"
    log_format: str = "json"
    enable_console_logging: bool = True
    enable_file_logging: bool = True
    log_file_path: str = "logs/health_assistant.log"
    log_file_max_size: int = 10 * 1024 * 1024  # 10MB
    log_file_backup_count: int = 5


class ResilienceSettings(BaseModel):
    """Resilience pattern settings"""

    enable_circuit_breaker: bool = True
    enable_retries: bool = True
    enable_timeouts: bool = True

    # Circuit breaker settings
    circuit_breaker_fail_max: int = 5
    circuit_breaker_reset_timeout: int = 30

    # Retry settings
    max_retry_attempts: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 60.0

    # Timeout settings
    default_timeout: float = 30.0
    api_timeout: float = 5.0
    database_timeout: float = 10.0


class SecuritySettings(BaseModel):
    """Security settings"""

    enable_mtls: bool = False
    require_client_cert: bool = False
    trusted_ca_certs: Optional[str] = None
    server_cert_path: Optional[str] = None
    server_key_path: Optional[str] = None
    client_cert_validation: bool = True

    # CORS settings
    cors_origins: List[str] = [
        "http://localhost:5173",  # React dev server
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:5173",  # React dev server with IP
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "*",  # Allow all origins in development
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: List[str] = ["*"]

    # Rate limiting settings
    enable_rate_limiting: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds

    # Security headers
    enable_security_headers: bool = True
    enable_csp: bool = True
    enable_hsts: bool = True

    def __init__(self, **data):
        # Workaround: directly read environment variables for CORS
        if "CORS_ORIGINS" in os.environ:
            cors_origins_str = os.environ["CORS_ORIGINS"]
            # Parse the JSON array string
            if cors_origins_str.startswith("[") and cors_origins_str.endswith("]"):
                # Remove brackets and split by comma, then strip quotes
                cors_origins = [
                    origin.strip().strip('"').strip("'")
                    for origin in cors_origins_str[1:-1].split(",")
                ]
                data["cors_origins"] = cors_origins

        super().__init__(**data)


class FeatureFlagSettings(BaseModel):
    """Feature flag settings"""

    enable_feature_flags: bool = True
    feature_flag_cache_ttl: int = 300  # 5 minutes
    enable_redis_backend: bool = True


class DeploymentSettings(BaseModel):
    """Deployment strategy settings"""

    enable_canary_releases: bool = False
    canary_percentage: int = 10
    enable_blue_green: bool = False
    enable_rollback: bool = True

    # Health check settings
    health_check_interval: int = 30  # seconds
    health_check_timeout: int = 5  # seconds
    health_check_retries: int = 3

    # Graceful shutdown
    graceful_shutdown_timeout: int = 30  # seconds


class DevelopmentSettings(BaseModel):
    """Development-specific settings"""

    debug: bool = True
    environment: str = "development"
    reload: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_prefix": ""}

    def __init__(self, **data):
        # Workaround: directly read environment variables
        if "ENVIRONMENT" in os.environ:
            data["environment"] = os.environ["ENVIRONMENT"]

        super().__init__(**data)


class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Application
    APP_NAME: str = "Personal Health Assistant"
    APP_VERSION: str = "1.0.0"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # Database
    DATABASE_URL: str = "postgresql://postgres:your-super-secret-and-long-postgres-password@localhost:5432/health_assistant"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_SIZE: int = 10

    # JWT
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # React dev server
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:5173",  # React dev server with IP
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    RATE_LIMIT_PER_MINUTE: int = 100

    # Supabase
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # Auth0
    AUTH0_DOMAIN: Optional[str] = None
    AUTH0_CLIENT_ID: Optional[str] = None
    AUTH0_CLIENT_SECRET: Optional[str] = None
    AUTH0_AUDIENCE: Optional[str] = None

    # External Services
    QDRANT_URL: str = "http://localhost:6333"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"

    # Neo4j Graph Database
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "your-super-secret-neo4j-password"

    # Observability
    PROMETHEUS_ENABLED: bool = True
    GRAFANA_ENABLED: bool = True
    TRACING_ENABLED: bool = True
    LOGGING_ENABLED: bool = True
    JAEGER_ENDPOINT: str = "http://localhost:4317"

    # Circuit Breaker
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60
    CIRCUIT_BREAKER_EXPECTED_EXCEPTION: str = "Exception"

    # API Gateway
    API_GATEWAY_URL: str = "http://localhost:8080"
    SERVICE_DISCOVERY_ENABLED: bool = True

    # Health Tracking
    HEALTH_TRACKING_SERVICE_URL: str = "http://localhost:8002"

    # User Profile
    USER_PROFILE_SERVICE_URL: str = "http://localhost:8001"

    # Auth Service
    AUTH_SERVICE_URL: str = "http://localhost:8000"

    # Device Data Service
    DEVICE_DATA_SERVICE_URL: str = "http://localhost:8004"

    # Medical Records Service
    MEDICAL_RECORDS_SERVICE_URL: str = "http://localhost:8005"

    # Voice Input Service
    VOICE_INPUT_SERVICE_URL: str = "http://localhost:8003"

    # Medical Analysis Service
    MEDICAL_ANALYSIS_SERVICE_URL: str = "http://localhost:8006"

    # Nutrition Service
    NUTRITION_SERVICE_URL: str = "http://localhost:8007"

    # Health Analysis Service
    HEALTH_ANALYSIS_SERVICE_URL: str = "http://localhost:8008"

    # AI Insights Service
    AI_INSIGHTS_SERVICE_URL: str = "http://localhost:8200"

    # AI Reasoning Orchestrator Service
    AI_REASONING_ORCHESTRATOR_URL: str = "http://localhost:8300"

    # GraphQL BFF Service
    GRAPHQL_BFF_URL: str = "http://localhost:8400"

    # Knowledge Graph Service
    KNOWLEDGE_GRAPH_SERVICE_URL: str = "http://localhost:8010"

    # Consent Audit Service
    CONSENT_AUDIT_SERVICE_URL: str = "http://localhost:8009"

    # Doctor Collaboration Service
    DOCTOR_COLLABORATION_SERVICE_URL: str = "http://localhost:8011"

    # Genomics Service
    GENOMICS_SERVICE_URL: str = "http://localhost:8012"

    # Analytics Service
    ANALYTICS_SERVICE_URL: str = "http://localhost:8210"

    # Ecommerce Service
    ECOMMERCE_SERVICE_URL: str = "http://localhost:8013"

    # Explainability Service
    EXPLAINABILITY_SERVICE_URL: str = "http://localhost:8014"

    # Email / SMTP
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_FROM: str = "noreply@healthassistant.com"
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # AI/ML API Keys
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # EPIC FHIR
    EPIC_FHIR_CLIENT_ID: Optional[str] = None
    EPIC_FHIR_CLIENT_SECRET: Optional[str] = None
    EPIC_FHIR_ENVIRONMENT: Optional[str] = None
    EPIC_FHIR_REDIRECT_URI: Optional[str] = None

    # Add nested settings for resilience and external_services
    resilience: ResilienceSettings = ResilienceSettings()
    external_services: ExternalServicesSettings = ExternalServicesSettings()
    security: SecuritySettings = None  # Will be initialized in __init__
    monitoring: MonitoringSettings = MonitoringSettings()
    development: DevelopmentSettings = DevelopmentSettings()
    auth: AuthSettings = AuthSettings()

    def __init__(self, **data):
        # Initialize security settings with CORS origins from environment
        if "security" not in data:
            cors_origins = [
                "http://localhost:5173",  # React dev server
                "http://localhost:3000",
                "http://localhost:8080",
                "http://127.0.0.1:5173",  # React dev server with IP
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8080",
                "*",  # Allow all origins in development
            ]
            if "CORS_ORIGINS" in os.environ:
                cors_origins_str = os.environ["CORS_ORIGINS"]
                # Handle empty or malformed CORS_ORIGINS
                if cors_origins_str and cors_origins_str.strip():
                    try:
                        import json

                        parsed = json.loads(cors_origins_str)
                        if isinstance(parsed, list):
                            cors_origins = parsed
                    except (json.JSONDecodeError, ValueError):
                        # Fallback to comma-separated parsing
                        if cors_origins_str.startswith(
                            "["
                        ) and cors_origins_str.endswith("]"):
                            cors_origins = [
                                origin.strip().strip('"').strip("'")
                                for origin in cors_origins_str[1:-1].split(",")
                                if origin.strip()
                            ]
                        else:
                            cors_origins = [
                                origin.strip()
                                for origin in cors_origins_str.split(",")
                                if origin.strip()
                            ]

            data["security"] = SecuritySettings(cors_origins=cors_origins)

        super().__init__(**data)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            # Handle empty string
            if not v.strip():
                return ["http://localhost:3000", "http://localhost:8080"]
            # Try to parse as JSON first
            try:
                import json

                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                pass
            # Fallback to comma-separated string
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            # Handle empty or malformed strings
            if not v.strip():
                return ["localhost", "127.0.0.1"]
            # Try to parse as JSON first
            try:
                import json

                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                pass
            # Fallback to comma-separated string
            return [host.strip() for host in v.split(",") if host.strip()]
        return v

    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def generate_secret_key(cls, v):
        if not v or v == "your-super-secret-key-change-in-production":
            return secrets.token_urlsafe(32)
        return v

    @field_validator("JWT_SECRET_KEY", mode="before")
    @classmethod
    def generate_jwt_secret_key(cls, v):
        if not v or v == "your-super-secret-jwt-key-change-in-production":
            return secrets.token_urlsafe(32)
        return v

    model_config = {"env_file": ".env", "case_sensitive": True, "extra": "allow"}


class AuthSettings(Settings):
    SERVICE_NAME: str = "auth-service"
    SERVICE_PORT: int = 8000


class UserProfileSettings(Settings):
    SERVICE_NAME: str = "user-profile-service"
    SERVICE_PORT: int = 8001


class HealthTrackingSettings(Settings):
    SERVICE_NAME: str = "health-tracking-service"
    SERVICE_PORT: int = 8002


class DeviceDataSettings(Settings):
    SERVICE_NAME: str = "device-data-service"
    SERVICE_PORT: int = 8004


class VoiceInputSettings(Settings):
    SERVICE_NAME: str = "voice-input-service"
    SERVICE_PORT: int = 8003


class MedicalAnalysisSettings(Settings):
    SERVICE_NAME: str = "medical-analysis-service"
    SERVICE_PORT: int = 8006


class APIGatewaySettings(Settings):
    SERVICE_NAME: str = "api-gateway"
    SERVICE_PORT: int = 8080


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings singleton"""
    global _settings
    if _settings is None:
        logger.info("Creating new Settings instance")
        _settings = Settings()
        logger.info("Settings instance created successfully")
    return _settings


def is_development() -> bool:
    """Check if running in development mode"""
    settings = get_settings()
    return settings.ENVIRONMENT == "development"


def is_production() -> bool:
    """Check if running in production mode"""
    settings = get_settings()
    return settings.ENVIRONMENT == "production"


def is_testing() -> bool:
    """Check if running in testing mode"""
    settings = get_settings()
    return settings.ENVIRONMENT == "testing"


def get_database_url() -> str:
    """Get database URL from settings"""
    settings = get_settings()
    logger.info(f"Getting database URL: {settings.DATABASE_URL}")
    return settings.DATABASE_URL


def get_log_level() -> str:
    """Get log level from settings"""
    settings = get_settings()
    return settings.LOG_LEVEL


def get_cors_origins() -> List[str]:
    """Get CORS origins from settings"""
    settings = get_settings()
    return settings.CORS_ORIGINS


def validate_required_settings():
    """Validate that all required settings are present"""
    settings = get_settings()
    logger.info("Validating required settings...")

    # Check database settings
    if not settings.DATABASE_URL:
        raise ValueError("Database URL is required")

    # Check auth settings
    if not settings.JWT_SECRET_KEY:
        raise ValueError("JWT secret key is required")

    logger.info("All required settings are valid")


# Initialize settings validation only if not in testing mode
if not is_testing():
    try:
        validate_required_settings()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print(
            "Please check your .env file and ensure all required settings are configured."
        )
        # Don't raise in development mode
        if is_production():
            raise

settings = get_settings()
