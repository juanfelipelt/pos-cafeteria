"""Seguridad: tokens JWT (JSON Web Token).

Este módulo crea y valida los tokens que sirven para autenticar al usuario en
cada petición. Cuando alguien inicia sesión, recibe un token firmado; en las
siguientes peticiones lo envía y el backend lo verifica.

Un JWT tiene tres partes y su contenido va firmado con la clave secreta
(settings.secret_key), de modo que no puede alterarse sin que la firma falle.

Relación con el resto:
- Los routers usan `create_access_token` al hacer login.
- Las dependencias de seguridad usan `decode_token` para saber quién es el
  usuario y qué rol tiene.

Las funciones no cambian el contenido del token: solo lo firman o lo validan.
"""

from datetime import datetime, timedelta, timezone

import jwt

from config import settings


def create_access_token(subject: str, rol: str) -> str:
    """Crea un token de acceso firmado.

    `subject` es el identificador del usuario (normalmente su id o email) y
    `rol` su rol. El token incluye cuándo se emitió (iat) y cuándo expira
    (exp) según la configuración.
    """
    # Momento actual en UTC, para las marcas de tiempo del token.
    now = datetime.now(timezone.utc)
    # Contenido (payload) que viajará dentro del token.
    payload = {
        "sub": subject,  # "subject": a quién representa el token.
        "rol": rol,      # Rol del usuario dentro del sistema.
        "iat": now,      # "issued at": fecha de emisión.
        # "exp": fecha de expiración (ahora + minutos configurados).
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    # Codificamos y firmamos el token con la clave secreta y el algoritmo.
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict:
    """Decodifica y verifica un token.

    Lanza una excepción de la librería `jwt` si el token es inválido, está
    alterado o expirado; si es correcto, devuelve el payload como diccionario.
    """
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
