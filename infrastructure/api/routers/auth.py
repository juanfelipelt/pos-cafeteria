from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.schemas.auth import LoginRequest, RegistrarRequest
from application.services.auth_service import AuthService
from database import get_session
from domain.entities.usuario import Usuario
from infrastructure.api.dependencies import get_current_user, require_admin
from infrastructure.repositories.usuario_repository import SQLAlchemyUsuarioRepository

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_session)):
    token = AuthService(SQLAlchemyUsuarioRepository(db), db).login(
        body.email, body.password
    )
    usuario = SQLAlchemyUsuarioRepository(db).get_by_email(body.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": usuario.to_dict(),
    }


@router.post("/registro")
def registrar(
    body: RegistrarRequest,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    usuario = AuthService(SQLAlchemyUsuarioRepository(db), db).registrar(
        body.nombre, body.email, body.password, body.rol
    )
    return usuario.to_dict()


@router.get("/me")
def me(usuario: Usuario = Depends(get_current_user)):
    return usuario.to_dict()


@router.get("/usuarios")
def listar_usuarios(
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    return [
        u.to_dict()
        for u in AuthService(SQLAlchemyUsuarioRepository(db), db).listar()
    ]
