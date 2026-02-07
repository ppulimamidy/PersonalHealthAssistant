"""
JWT Service for Epic FHIR Integration

This module provides JWT generation, validation, and JWK set management
for Epic FHIR integration requirements.
"""

import jwt
import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key
import base64
import hashlib
import os

from common.utils.logging import get_logger

logger = get_logger(__name__)


class JWKService:
    """JSON Web Key service for Epic FHIR integration."""
    
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self.key_id = None
        self.jwk_set = None
        self.certificate = None
        self._load_or_generate_keys_and_cert()
    
    def _load_or_generate_keys_and_cert(self):
        """Load existing keys/cert or generate new ones."""
        try:
            self._load_keys_and_cert_from_env_or_file()
        except Exception as e:
            logger.warning(f"Could not load existing keys/cert: {e}")
            logger.info("Generating new RSA key pair and self-signed certificate for Epic FHIR JWT validation")
            self._generate_new_keys_and_cert()
    
    def _load_keys_and_cert_from_env_or_file(self):
        """Load keys and certificate from environment variables or files."""
        private_key_pem = os.getenv("EPIC_FHIR_PRIVATE_KEY")
        public_key_pem = os.getenv("EPIC_FHIR_PUBLIC_KEY")
        key_id = os.getenv("EPIC_FHIR_KEY_ID")
        cert_pem = os.getenv("EPIC_FHIR_CERTIFICATE")
        private_key_path = os.getenv("EPIC_FHIR_PRIVATE_KEY_PATH")
        cert_path = os.getenv("EPIC_FHIR_CERTIFICATE_PATH")
        
        if private_key_path and os.path.exists(private_key_path):
            with open(private_key_path, "r") as f:
                private_key_pem = f.read()
        if cert_path and os.path.exists(cert_path):
            with open(cert_path, "r") as f:
                cert_pem = f.read()
        
        if private_key_pem and cert_pem:
            self.private_key = load_pem_private_key(
                private_key_pem.encode(),
                password=None,
                backend=default_backend()
            )
            self.public_key = self.private_key.public_key()
            self.certificate = cert_pem
            self.key_id = key_id or self._extract_key_id_from_cert(cert_pem) or f"epic-fhir-{secrets.token_hex(8)}"
            logger.info("Loaded existing RSA keys and certificate from environment or file")
        else:
            raise ValueError("Missing required private key or certificate for JWT keys")
    
    def _generate_new_keys_and_cert(self):
        # Fallback: generate keys and a placeholder cert (not for production)
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
        self.key_id = f"epic-fhir-{secrets.token_hex(8)}"
        self.certificate = self._generate_placeholder_certificate()
        self._generate_jwk_set()
        self._save_keys_and_cert_to_env()
        logger.info(f"Generated new RSA key pair with key ID: {self.key_id}")
    
    def _save_keys_and_cert_to_env(self):
        private_key_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()
        public_key_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
        os.environ["EPIC_FHIR_PRIVATE_KEY"] = private_key_pem
        os.environ["EPIC_FHIR_PUBLIC_KEY"] = public_key_pem
        os.environ["EPIC_FHIR_KEY_ID"] = self.key_id
        os.environ["EPIC_FHIR_CERTIFICATE"] = self.certificate
        logger.info("Saved RSA keys and certificate to environment variables")
    
    def _generate_placeholder_certificate(self) -> str:
        # This is a placeholder. In production, always use a real X.509 cert.
        return "-----BEGIN CERTIFICATE-----\n" + base64.b64encode(b"placeholder-certificate").decode() + "\n-----END CERTIFICATE-----"
    
    def _extract_key_id_from_cert(self, cert_pem: str) -> str:
        # Optionally extract a key ID from the certificate (not required)
        return None
    
    def _generate_jwk_set(self):
        public_numbers = self.public_key.public_numbers()
        def int_to_base64url(value):
            byte_length = (value.bit_length() + 7) // 8
            value_bytes = value.to_bytes(byte_length, byteorder='big')
            return base64.urlsafe_b64encode(value_bytes).decode('utf-8').rstrip('=')
        # Read the certificate and base64 encode it (strip PEM headers)
        x5c = []
        if self.certificate:
            cert_lines = [line for line in self.certificate.splitlines() if "CERTIFICATE" not in line and line.strip()]
            cert_b64 = ''.join(cert_lines)
            x5c = [cert_b64]
        jwk = {
            "kty": "RSA",
            "kid": self.key_id,
            "use": "sig",
            "alg": "RS256",
            "n": int_to_base64url(public_numbers.n),
            "e": int_to_base64url(public_numbers.e),
            "x5c": x5c,
            "x5t": self._get_thumbprint()
        }
        self.jwk_set = {"keys": [jwk]}
        logger.info("Generated JWK Set for Epic FHIR with certificate")
    
    def _get_x509_certificate(self) -> str:
        """Get X.509 certificate (simplified for demo)."""
        # In a real implementation, you would generate a proper X.509 certificate
        # For now, we'll create a placeholder
        return base64.b64encode(b"placeholder-certificate").decode()
    
    def _get_thumbprint(self) -> str:
        """Get X.509 certificate thumbprint."""
        # In a real implementation, you would calculate the actual thumbprint
        # For now, we'll create a placeholder
        return base64.urlsafe_b64encode(b"placeholder-thumbprint").decode().rstrip('=')
    
    def get_jwk_set(self) -> Dict[str, Any]:
        """Get the JSON Web Key Set."""
        if not self.jwk_set:
            self._generate_jwk_set()
        return self.jwk_set
    
    def get_jwk_set_url(self) -> str:
        """Get the JWK Set URL."""
        # Get the service URL from environment or use default
        service_url = os.getenv("MEDICAL_RECORDS_SERVICE_URL", "http://localhost:8005")
        return f"{service_url}/api/v1/medical-records/epic-fhir/.well-known/jwks.json"
    
    def generate_jwt(self, claims: Dict[str, Any], expires_in: int = 3600) -> str:
        """Generate a JWT token for Epic FHIR."""
        try:
            # Prepare claims
            now = datetime.utcnow()
            payload = {
                "iss": "personal-health-assistant",  # Your application identifier
                "sub": claims.get("sub", "system"),  # Subject (user or system)
                "aud": "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token",  # Epic token endpoint
                "iat": int(now.timestamp()),  # Issued at
                "exp": int((now + timedelta(seconds=expires_in)).timestamp()),  # Expiration
                "jti": secrets.token_hex(16),  # JWT ID
                **claims  # Additional claims
            }
            
            # Generate JWT
            token = jwt.encode(
                payload,
                self.private_key,
                algorithm="RS256",
                headers={
                    "kid": self.key_id,
                    "typ": "JWT"
                }
            )
            
            logger.info(f"Generated JWT for Epic FHIR with subject: {payload['sub']}")
            return token
            
        except Exception as e:
            logger.error(f"Failed to generate JWT: {e}")
            raise
    
    def verify_jwt(self, token: str) -> Dict[str, Any]:
        """Verify a JWT token."""
        try:
            # Decode and verify JWT
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=["RS256"],
                audience="https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token",
                issuer="personal-health-assistant"
            )
            
            logger.info(f"Verified JWT for Epic FHIR with subject: {payload.get('sub')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.error("JWT token has expired")
            raise
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid JWT token: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to verify JWT: {e}")
            raise
    
    def get_public_key_pem(self) -> str:
        """Get the public key in PEM format."""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
    
    def get_private_key_pem(self) -> str:
        """Get the private key in PEM format."""
        return self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()


# Global JWK service instance
jwk_service = JWKService() 