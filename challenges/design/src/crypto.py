import os
import secrets
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Pull the master secret directly from deployment environment context configuration
MASTER_SECRET = os.getenv("MASTER_SECRET", "fallback_default_insecure_secret_32_bytes!!").encode()

def derive_encryption_key(salt: bytes) -> bytes:
    """
    Derives a localized unique AES key per cryptographic transaction utilizing HKDF-SHA256.
    """
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=b"api-key-service-encryption-context",
    )
    return hkdf.derive(MASTER_SECRET)

def encrypt_key_data(plain_text_key: str) -> tuple[str, str]:
    """
    Encrypts the plaintext API key via authenticated AES-256-GCM.
    Returns: (hex_ciphertext, hex_nonce)
    """
    nonce = secrets.token_bytes(12)  # Cryptographically secure 96-bit nonce requirement
    key = derive_encryption_key(nonce)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plain_text_key.encode("utf-8"), None)
    return ciphertext.hex(), nonce.hex()

def decrypt_key_data(ciphertext_hex: str, nonce_hex: str) -> str:
    """
    Decrypts the ciphertext back to plaintext.
    """
    nonce = bytes.fromhex(nonce_hex)
    ciphertext = bytes.fromhex(ciphertext_hex)
    key = derive_encryption_key(nonce)
    aesgcm = AESGCM(key)
    decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    return decrypted_bytes.decode("utf-8")
