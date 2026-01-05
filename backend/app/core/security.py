import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import settings

def _get_start_key() -> bytes:
    """Derives a valid 32-byte url-safe base64-encoded key from the SECRET_KEY."""
    # This ensures that even if SECRET_KEY is just a random string, we get a valid Fernet key
    # that persists across restarts (as long as SECRET_KEY is constant).
    secret = settings.SECRET_KEY.encode()
    # Use SHA256 to get 32 bytes
    digest = hashlib.sha256(secret).digest()
    # Base64 encode it to be url-safe, which Fernet requires
    return base64.urlsafe_b64encode(digest)

try:
    _fernet_key = _get_start_key()
    cipher_suite = Fernet(_fernet_key)
except Exception as e:
    # Fallback only if something catastrophic happens, though the derivation above should be safe
    print(f"CRITICAL SECURITY WARNING: Could not derive key from SECRET_KEY. Using temporary random key. Error: {e}")
    cipher_suite = Fernet(Fernet.generate_key())

def encrypt_data(text: str) -> bytes:
    """Encrypts a string into bytes."""
    if text is None:
        return b""
    return cipher_suite.encrypt(str(text).encode())

def decrypt_data(data: bytes) -> str:
    """Decrypts bytes back into a string."""
    if not data:
        return ""
    try:
        return cipher_suite.decrypt(data).decode()
    except Exception:
        # In case of key rotation or corruption, better to return an error marker than crash
        return "[ERROR: DECRYPTION FAILED]"

def hash_user_id(raw_id: str) -> str:
    """Hashes a user ID using SHA-256 for anonymization."""
    if not raw_id:
        return ""
    return hashlib.sha256(str(raw_id).encode()).hexdigest()
