import hashlib
import hmac
import os

_ITERATIONS = 260_000
_LEGACY_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _ITERATIONS
    )
    return f"pbkdf2_sha256${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    parts = hashed.split("$")
    try:
        if len(parts) == 2:
            salt_hex, digest_hex = parts
            iterations = _LEGACY_ITERATIONS
        elif len(parts) == 4:
            _, iter_str, salt_hex, digest_hex = parts
            iterations = int(iter_str)
        else:
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except (ValueError, TypeError):
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return hmac.compare_digest(digest, expected)
