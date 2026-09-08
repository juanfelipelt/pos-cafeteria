import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from application.security.jwt import decode_token
from database import get_session
from domain.entities.enums import Rol
from domain.entities.usuario import Usuario
from infrastructure.repositories.usuario_repository import SQLAlchemyUsuarioRepository

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_session),
) -> Usuario:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No autenticado.")

    try:
        payload = decode_token(credentials.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido o expirado.")

    usuario = SQLAlchemyUsuarioRepository(db).get(payload.get("sub"))
    if usuario is None or not usuario.estado:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario no válido.")
    return usuario


def require_admin(
    usuario: Usuario = Depends(get_current_user),
) -> Usuario:
    if usuario.rol != Rol.ADMIN:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Requiere rol administrador."
        )
    return usuario
