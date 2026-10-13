"""
Dependencias reutilizables para la capa de API (FastAPI).

¿Qué es una "dependencia" en FastAPI?
Es una función que FastAPI ejecuta automáticamente ANTES de llamar a tu
endpoint, para preparar cosas que muchos endpoints necesitan (por ejemplo,
saber qué usuario está conectado). Se declaran con `Depends(...)`.

Este archivo concentra dos dependencias muy usadas en todo el proyecto:

1. `get_current_user`: valida el token JWT y devuelve el usuario autenticado.
2. `require_admin`: exige que ese usuario tenga rol de administrador.

Así evitamos repetir la misma verificación de seguridad en cada router.
"""

# `jwt` se usa para detectar errores al decodificar el token del usuario.
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from application.security.jwt import decode_token
from database import get_session
from domain.entities.enums import Rol
from domain.entities.usuario import Usuario
from infrastructure.repositories.usuario_repository import SQLAlchemyUsuarioRepository

# Esquema de seguridad HTTP Bearer. `auto_error=False` indica que, si no llega
# el encabezado "Authorization: Bearer <token>", NO lancamos error aquí
# automáticamente: nosotros decidimos el mensaje más abajo (así damos un 401
# claro y en español en lugar del error genérico de FastAPI).
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_session),
) -> Usuario:
    """
    Obtiene el usuario autenticado a partir del token JWT enviado.

    ¿Cómo funciona?
    1. FastAPI extrae el token del encabezado Authorization (Bearer).
    2. Se decodifica el token; si es inválido o expiró, se rechaza.
    3. Con el identificador (`sub`) del token se busca el usuario en BD.
    4. Se verifica que exista y que su estado sea activo.

    Parámetros:
        credentials: Credenciales Bearer que FastAPI inyecta desde el header.
        db: Sesión de base de datos que FastAPI inyecta.

    Respuesta:
        La entidad `Usuario` ya autenticada.

    Nivel de acceso:
        Requiere un token válido; si falta o es inválido => HTTP 401.
    """
    # Sin credenciales no hay forma de autenticar: cortamos con 401.
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No autenticado.")

    try:
        # Decodificamos el token para leer su contenido (payload).
        payload = decode_token(credentials.credentials)
    except jwt.PyJWTError:
        # Cualquier problema con el token (firma, formato, expiración) => 401.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido o expirado.")

    # Buscamos al usuario usando el campo "sub" (subject) del token, que
    # normalmente guarda el id o email del usuario.
    usuario = SQLAlchemyUsuarioRepository(db).get(payload.get("sub"))
    # Si no existe, o fue desactivado, negamos el acceso.
    if usuario is None or not usuario.estado:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario no válido.")
    return usuario


def require_admin(
    usuario: Usuario = Depends(get_current_user),
) -> Usuario:
    """
    Dependencia que exige que el usuario autenticado sea administrador.

    Reutiliza `get_current_user` (así primero garantiza la autenticación) y
    luego comprueba el rol.

    Parámetros:
        usuario: El usuario ya autenticado, inyectado por get_current_user.

    Respuesta:
        El mismo usuario, si es administrador.

    Nivel de acceso:
        Solo rol ADMIN; en caso contrario => HTTP 403 (prohibido).
    """
    # Si el rol no es ADMIN, no tiene permisos para operaciones sensibles.
    if usuario.rol != Rol.ADMIN:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Requiere rol administrador."
        )
    return usuario
