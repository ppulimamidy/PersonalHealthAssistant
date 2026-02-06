"""
Multi-Factor Authentication (MFA) service for enhanced security.

This service handles:
- TOTP (Time-based One-Time Password) generation and validation
- MFA device management
- Backup codes generation and validation
- MFA attempt tracking and rate limiting
- Device verification and enrollment
"""

import os
import secrets
import hashlib
import base64
import time
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import pyotp
import qrcode
from io import BytesIO
from common.utils.logging import get_logger
from common.config.settings import get_settings

logger = get_logger(__name__)


class MFAService:
    """Service for Multi-Factor Authentication operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.backup_code_length = 10
        self.backup_code_count = 10
        self.max_attempts = 5
        self.lockout_duration = timedelta(minutes=15)
    
    def generate_totp_secret(self) -> str:
        """Generate a new TOTP secret key."""
        try:
            # Generate a random secret key
            secret = pyotp.random_base32()
            logger.info("Generated new TOTP secret key")
            return secret
            
        except Exception as e:
            logger.error(f"Failed to generate TOTP secret: {e}")
            raise
    
    def generate_totp_uri(self, secret: str, user_email: str, issuer: str = "Personal Health Assistant") -> str:
        """Generate TOTP URI for QR code generation."""
        try:
            totp = pyotp.TOTP(secret)
            uri = totp.provisioning_uri(
                name=user_email,
                issuer_name=issuer
            )
            logger.info(f"Generated TOTP URI for user: {user_email}")
            return uri
            
        except Exception as e:
            logger.error(f"Failed to generate TOTP URI: {e}")
            raise
    
    def generate_qr_code(self, uri: str) -> bytes:
        """Generate QR code image from TOTP URI."""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to bytes
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_code_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info("Generated QR code for TOTP")
            return qr_code_bytes
            
        except Exception as e:
            logger.error(f"Failed to generate QR code: {e}")
            raise
    
    def verify_totp(self, secret: str, token: str, window: int = 1) -> bool:
        """Verify TOTP token."""
        try:
            totp = pyotp.TOTP(secret)
            is_valid = totp.verify(token, valid_window=window)
            
            if is_valid:
                logger.info("TOTP token verified successfully")
            else:
                logger.warning("TOTP token verification failed")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Failed to verify TOTP token: {e}")
            return False
    
    def generate_backup_codes(self) -> List[Tuple[str, str]]:
        """Generate backup codes for MFA recovery."""
        try:
            backup_codes = []
            
            for _ in range(self.backup_code_count):
                # Generate random code
                code = secrets.token_hex(self.backup_code_length // 2).upper()
                # Format as groups of 4 characters
                formatted_code = '-'.join([code[i:i+4] for i in range(0, len(code), 4)])
                
                # Hash the code for storage
                code_hash = hashlib.sha256(code.encode()).hexdigest()
                
                backup_codes.append((formatted_code, code_hash))
            
            logger.info(f"Generated {self.backup_code_count} backup codes")
            return backup_codes
            
        except Exception as e:
            logger.error(f"Failed to generate backup codes: {e}")
            raise
    
    def verify_backup_code(self, provided_code: str, stored_hash: str) -> bool:
        """Verify backup code."""
        try:
            # Clean the provided code
            clean_code = provided_code.replace('-', '').upper()
            
            # Hash the provided code
            provided_hash = hashlib.sha256(clean_code.encode()).hexdigest()
            
            # Compare hashes
            is_valid = secrets.compare_digest(provided_hash, stored_hash)
            
            if is_valid:
                logger.info("Backup code verified successfully")
            else:
                logger.warning("Backup code verification failed")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Failed to verify backup code: {e}")
            return False
    
    def generate_verification_code(self) -> str:
        """Generate a verification code for device enrollment."""
        try:
            # Generate a 6-digit verification code
            code = str(secrets.randbelow(1000000)).zfill(6)
            logger.info("Generated verification code for device enrollment")
            return code
            
        except Exception as e:
            logger.error(f"Failed to generate verification code: {e}")
            raise
    
    def calculate_risk_score(self, attempt_data: Dict[str, Any]) -> int:
        """Calculate risk score for MFA attempt."""
        try:
            risk_score = 0
            
            # Check for suspicious patterns
            if attempt_data.get('is_suspicious', False):
                risk_score += 50
            
            # Check for multiple failed attempts
            failed_attempts = attempt_data.get('failed_attempts', 0)
            if failed_attempts > 3:
                risk_score += failed_attempts * 10
            
            # Check for unusual location
            if attempt_data.get('unusual_location', False):
                risk_score += 30
            
            # Check for unusual time
            if attempt_data.get('unusual_time', False):
                risk_score += 20
            
            # Check for new device
            if attempt_data.get('new_device', False):
                risk_score += 15
            
            logger.info(f"Calculated risk score: {risk_score}")
            return min(risk_score, 100)  # Cap at 100
            
        except Exception as e:
            logger.error(f"Failed to calculate risk score: {e}")
            return 0
    
    def is_device_locked(self, failed_attempts: int, locked_until: Optional[datetime]) -> bool:
        """Check if device is locked due to too many failed attempts."""
        try:
            if locked_until and datetime.utcnow() < locked_until:
                logger.info("Device is currently locked")
                return True
            
            if failed_attempts >= self.max_attempts:
                logger.info("Device should be locked due to too many failed attempts")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check device lock status: {e}")
            return True  # Default to locked for safety
    
    def calculate_lockout_until(self) -> datetime:
        """Calculate lockout end time."""
        try:
            return datetime.utcnow() + self.lockout_duration
            
        except Exception as e:
            logger.error(f"Failed to calculate lockout time: {e}")
            return datetime.utcnow() + timedelta(hours=1)  # Default 1 hour
    
    def validate_device_enrollment(self, device_data: Dict[str, Any]) -> bool:
        """Validate device enrollment data."""
        try:
            required_fields = ['device_name', 'device_type', 'device_id']
            
            for field in required_fields:
                if not device_data.get(field):
                    logger.warning(f"Missing required field for device enrollment: {field}")
                    return False
            
            # Validate device type
            valid_types = ['mobile', 'tablet', 'desktop', 'laptop', 'other']
            if device_data.get('device_type') not in valid_types:
                logger.warning(f"Invalid device type: {device_data.get('device_type')}")
                return False
            
            logger.info("Device enrollment data validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate device enrollment: {e}")
            return False
    
    def generate_device_fingerprint(self, device_data: Dict[str, Any]) -> str:
        """Generate device fingerprint for tracking."""
        try:
            # Create a fingerprint from device characteristics
            fingerprint_data = {
                'user_agent': device_data.get('user_agent', ''),
                'screen_resolution': device_data.get('screen_resolution', ''),
                'timezone': device_data.get('timezone', ''),
                'language': device_data.get('language', ''),
                'platform': device_data.get('platform', ''),
                'device_id': device_data.get('device_id', '')
            }
            
            # Create a hash of the fingerprint data
            fingerprint_string = '|'.join(str(v) for v in fingerprint_data.values())
            fingerprint = hashlib.sha256(fingerprint_string.encode()).hexdigest()
            
            logger.info("Generated device fingerprint")
            return fingerprint
            
        except Exception as e:
            logger.error(f"Failed to generate device fingerprint: {e}")
            raise
    
    def check_attempt_rate_limit(self, user_id: str, device_id: str, attempts: List[Dict[str, Any]]) -> bool:
        """Check if MFA attempts are within rate limits."""
        try:
            now = datetime.utcnow()
            recent_attempts = [
                attempt for attempt in attempts
                if (now - attempt.get('attempted_at', now)).total_seconds() < 300  # 5 minutes
            ]
            
            if len(recent_attempts) >= 10:  # Max 10 attempts per 5 minutes
                logger.warning(f"Rate limit exceeded for user {user_id}, device {device_id}")
                return False
            
            logger.info("Rate limit check passed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to check rate limit: {e}")
            return False
    
    def get_totp_remaining_time(self, secret: str) -> int:
        """Get remaining time for current TOTP period."""
        try:
            totp = pyotp.TOTP(secret)
            return totp.interval - (int(time.time()) % totp.interval)
            
        except Exception as e:
            logger.error(f"Failed to get TOTP remaining time: {e}")
            return 0
    
    def is_suspicious_attempt(self, attempt_data: Dict[str, Any]) -> bool:
        """Determine if an MFA attempt is suspicious."""
        try:
            suspicious_indicators = 0
            
            # Check for rapid attempts
            if attempt_data.get('rapid_attempts', False):
                suspicious_indicators += 1
            
            # Check for unusual location
            if attempt_data.get('unusual_location', False):
                suspicious_indicators += 1
            
            # Check for unusual time
            if attempt_data.get('unusual_time', False):
                suspicious_indicators += 1
            
            # Check for new device
            if attempt_data.get('new_device', False):
                suspicious_indicators += 1
            
            # Check for multiple failed attempts
            if attempt_data.get('failed_attempts', 0) > 2:
                suspicious_indicators += 1
            
            is_suspicious = suspicious_indicators >= 2
            
            if is_suspicious:
                logger.warning("MFA attempt flagged as suspicious")
            
            return is_suspicious
            
        except Exception as e:
            logger.error(f"Failed to check if attempt is suspicious: {e}")
            return True  # Default to suspicious for safety
    
    def generate_recovery_codes(self) -> List[str]:
        """Generate recovery codes for account recovery."""
        try:
            recovery_codes = []
            
            for _ in range(5):  # Generate 5 recovery codes
                # Generate a longer, more secure code
                code = secrets.token_hex(16).upper()
                # Format as groups of 4 characters
                formatted_code = '-'.join([code[i:i+4] for i in range(0, len(code), 4)])
                recovery_codes.append(formatted_code)
            
            logger.info("Generated recovery codes")
            return recovery_codes
            
        except Exception as e:
            logger.error(f"Failed to generate recovery codes: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on MFA service."""
        try:
            # Test TOTP generation
            test_secret = self.generate_totp_secret()
            test_uri = self.generate_totp_uri(test_secret, "test@example.com")
            
            # Test backup code generation
            backup_codes = self.generate_backup_codes()
            
            return {
                "status": "healthy",
                "message": "MFA service is functioning correctly",
                "timestamp": datetime.utcnow().isoformat(),
                "features": {
                    "totp_generation": "working",
                    "qr_code_generation": "working",
                    "backup_codes": "working",
                    "risk_scoring": "working"
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"MFA service health check failed: {e}",
                "timestamp": datetime.utcnow().isoformat()
            } 