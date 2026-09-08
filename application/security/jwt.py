from datetime import datetime, timedelta, timezone

import jwt

from config import settings


def create_access_token(subject: str, rol: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "rol": rol,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
