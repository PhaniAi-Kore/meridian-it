import secrets
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def derive_key(salt: bytes, master_secret: bytes) -> bytes:
    """Derives a cryptographically strong unique key per record using HKDF."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=b"api-key-issuance-metadata",
    )
    return hkdf.derive(master_secret)

def encrypt_data(plain_text: str, master_secret: bytes) -> tuple[str, str]:
    """Encrypts metadata via AES-GCM and returns (hex_ciphertext, hex_nonce)."""
    nonce = secrets.token_bytes(12)
    key = derive_key(nonce, master_secret)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plain_text.encode(), None)
    return ciphertext.hex(), nonce.hex()
