"""
TOTP Code Generation
Generates Time-based One-Time Passwords from base32 secrets
"""
import base64
import hmac
import hashlib
import time
import struct
import logging

# Logger configuré pour ne pas afficher les secrets
logger = logging.getLogger(__name__)

def generate_totp_code(secret: str, time_interval: int = 30) -> str:
    """
    Generate TOTP code from base32 secret

    Args:
        secret: Base32 encoded secret key
        time_interval: Time interval in seconds (default 30)

    Returns:
        6-digit TOTP code as string
    """
    try:
        # Clean and normalize secret
        secret = secret.upper().replace(' ', '')

        # Determine hash algorithm based on secret length
        algorithm = hashlib.sha1 if len(secret) <= 32 else hashlib.sha256

        # Add padding if needed
        padding = (8 - len(secret) % 8) % 8
        secret_padded = secret + '=' * padding

        # Base32 decode
        try:
            key = base64.b32decode(secret_padded)
        except Exception:
            return ""

        # Get current time counter
        time_counter = int(time.time() / time_interval)

        # Pack time counter as 8-byte big-endian
        time_bytes = struct.pack('>Q', time_counter)

        # Generate HMAC
        hmac_hash = hmac.new(key, time_bytes, algorithm).digest()

        # Dynamic truncation
        offset = hmac_hash[-1] & 0x0f
        code = struct.unpack('>I', hmac_hash[offset:offset+4])[0]
        code = (code & 0x7fffffff) % 1000000

        # Return as 6-digit string with leading zeros
        return str(code).zfill(6)

    except Exception:
        # Ne pas logger les détails pour éviter d'exposer des secrets
        logger.debug("TOTP generation failed - invalid secret format")
        return ""

def validate_base32_secret(secret: str) -> tuple[bool, str]:
    """
    Validate base32 secret format

    Returns:
        Tuple of (is_valid, error_message)
    """
    secret = secret.upper().replace(' ', '')

    if len(secret) < 16:
        return False, "Secret key too short (minimum 16 characters)"

    # Check valid base32 characters
    valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567=')
    if not all(c in valid_chars for c in secret):
        return False, "Invalid characters (must be A-Z, 2-7)"

    return True, ""
