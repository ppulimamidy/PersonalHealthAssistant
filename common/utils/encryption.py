"""
Field-level encryption for Protected Health Information (PHI).

Uses Fernet (AES-128-CBC + HMAC-SHA256) symmetric encryption.
Encrypted values are prefixed with 'enc:' to distinguish them from plaintext.

Environment variable: PHI_ENCRYPTION_KEY
Generate a key: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Usage:
    from common.utils.encryption import encrypt_phi, decrypt_phi, encrypt_dict_fields, decrypt_dict_fields

    # Single value
    encrypted = encrypt_phi("Metformin 500mg")
    plaintext = decrypt_phi(encrypted)

    # Dict fields
    row = {"medication_name": "Metformin", "dosage": "500mg", "user_id": "abc"}
    encrypted_row = encrypt_dict_fields(row, ["medication_name", "dosage"])
    decrypted_row = decrypt_dict_fields(encrypted_row, ["medication_name", "dosage"])
"""

import os
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_ENC_PREFIX = "enc:"
_fernet = None


def _get_fernet():
    """Lazy-initialize Fernet cipher from environment variable."""
    global _fernet
    if _fernet is not None:
        return _fernet

    key = os.getenv("PHI_ENCRYPTION_KEY")
    if not key:
        logger.warning(
            "PHI_ENCRYPTION_KEY not set — field-level encryption disabled. "
            "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
        return None

    try:
        from cryptography.fernet import Fernet

        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
        return _fernet
    except Exception as exc:
        logger.error("Failed to initialize Fernet cipher: %s", exc)
        return None


def encrypt_phi(value: Any) -> Any:
    """
    Encrypt a single PHI value. Returns prefixed ciphertext.
    If encryption is not configured, returns the value unchanged.
    Non-string values are converted to string, encrypted, then returned.
    """
    if value is None:
        return None

    f = _get_fernet()
    if f is None:
        return value  # graceful degradation — no encryption key configured

    plaintext = str(value)
    if plaintext.startswith(_ENC_PREFIX):
        return value  # already encrypted

    try:
        encrypted = f.encrypt(plaintext.encode("utf-8")).decode("utf-8")
        return f"{_ENC_PREFIX}{encrypted}"
    except Exception as exc:
        logger.error("PHI encryption failed: %s", exc)
        return value  # fail open to avoid data loss


def decrypt_phi(value: Any) -> Any:
    """
    Decrypt a single PHI value. Returns plaintext.
    If value is not encrypted (no prefix), returns as-is.
    """
    if value is None:
        return None

    if not isinstance(value, str) or not value.startswith(_ENC_PREFIX):
        return value  # not encrypted

    f = _get_fernet()
    if f is None:
        logger.warning("Cannot decrypt — PHI_ENCRYPTION_KEY not set")
        return value  # return ciphertext as-is

    try:
        ciphertext = value[len(_ENC_PREFIX) :]
        return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except Exception as exc:
        logger.error("PHI decryption failed: %s", exc)
        return value  # return as-is on failure


def encrypt_dict_fields(
    data: Dict[str, Any], fields: List[str]
) -> Dict[str, Any]:
    """Encrypt specific fields in a dictionary. Returns a new dict."""
    result = dict(data)
    for field in fields:
        if field in result and result[field] is not None:
            result[field] = encrypt_phi(result[field])
    return result


def decrypt_dict_fields(
    data: Dict[str, Any], fields: List[str]
) -> Dict[str, Any]:
    """Decrypt specific fields in a dictionary. Returns a new dict."""
    result = dict(data)
    for field in fields:
        if field in result and result[field] is not None:
            result[field] = decrypt_phi(result[field])
    return result


def is_encryption_enabled() -> bool:
    """Check if PHI encryption is configured."""
    return _get_fernet() is not None


# Fields that should be encrypted per table
PHI_FIELDS = {
    "medications": ["medication_name", "dosage", "prescribing_doctor", "pharmacy", "notes"],
    "supplements": ["supplement_name", "dosage", "brand", "purpose"],
    "symptom_journal": ["symptom_name", "notes", "location"],
    "health_conditions": ["condition_name", "notes"],
    "lab_results": ["ai_summary", "lab_name", "ordering_provider"],
    "meal_logs": ["meal_name", "meal_description", "user_notes"],
    "weekly_checkins": ["notes"],
    "care_plans": ["title", "notes"],
}
