"""
Router de autenticación y gestión de usuarios.

Recurso que expone: la identidad de las personas que usan el sistema
(usuarios) y su acceso (inicio de sesión).

Prefijo base de las rutas: `/auth`

Endpoints:
- POST /auth/login      -> inicia sesión y devuelve un token JWT.
- POST /auth/registro   -> crea un nuevo usuario (solo administrador).
- GET  /auth/me         -> devuelve los datos del usuario autenticado.
- GET  /auth/usuarios   -> lista todos los usuarios (solo administrador).

Nota pedagógica: el token JWT es como una "credencial firmada" que el cliente
debe enviar en cada petición para demostrar quién es.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from application.schemas.auth import LoginRequest, RegistrarRequest
from application.security.rate_limit import login_limiter
from application.services.auth_service import AuthService
from database import get_session
from domain.entities.usuario import Usuario
from infrastructure.api.dependencies import get_current_user, require_admin
from infrastructure.repositories.usuario_repository import SQLAlchemyUsuarioRepository

# Agrupamos todas las rutas bajo el prefijo "/auth" y las etiquetamos para
# que aparezcan juntas en la documentación automática (Swagger/OpenAPI).
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_session)):
    """
    Inicia sesión con email y contraseña.

    Parámetros:
        body: Datos de entrada (email y password) validados por LoginRequest.
        db: Sesión de base de datos inyectada por FastAPI.

    Respuesta:
        Un objeto con `access_token` (el token JWT), `token_type` ("bearer")
        y los datos del usuario.

    Nivel de acceso:
        Público (no requiere token), pero limitado por un control de intentos
        para evitar ataques de fuerza bruta.
    """
    # Normalizamos el email: quitamos espacios y lo pasamos a minúsculas para
    # que "Ana@X.com" y "ana@x.com" se traten igual.
    email = body.email.strip().lower()
    # El limitador cuenta intentos por email. Si se supera el máximo permitido
    # en un intervalo, bloqueamos temporalmente (HTTP 429 = demasiadas peticiones).
    if not login_limiter.allow(email):
        raise HTTPException(
            status_code=429, detail="Demasiados intentos. Intenta de nuevo más tarde."
        )

    # Delegamos la verificación de credenciales al servicio de autenticación.
    # Si las credenciales son incorrectas, el servicio lanza la excepción.
    token = AuthService(SQLAlchemyUsuarioRepository(db), db).login(
        body.email, body.password
    )
    # Login exitoso: reiniciamos el contador de intentos de ese email.
    login_limiter.reset(email)

    # Volvemos a buscar el usuario para devolver sus datos junto al token.
    usuario = SQLAlchemyUsuarioRepository(db).get_by_email(email)
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
    """
    Registra un nuevo usuario en el sistema.

    Parámetros:
        body: Nombre, email, password y rol del nuevo usuario.
        _: Dependencia que exige rol administrador (no usamos su valor, solo
           que se cumpla la verificación).
        db: Sesión de base de datos.

    Respuesta:
        Los datos del usuario creado (sin datos sensibles) en formato dict.

    Nivel de acceso:
        Solo administradores.
    """
    # Creamos el usuario mediante el servicio correspondiente.
    usuario = AuthService(SQLAlchemyUsuarioRepository(db), db).registrar(
        body.nombre, body.email, body.password, body.rol
    )
    return usuario.to_dict()


@router.get("/me")
def me(usuario: Usuario = Depends(get_current_user)):
    """
    Devuelve los datos del usuario que está conectado actualmente.

    Parámetros:
        usuario: Usuario autenticado, inyectado por la dependencia.

    Respuesta:
        Los datos del usuario en formato dict.

    Nivel de acceso:
        Cualquier usuario autenticado (token válido).
    """
    # `usuario` ya viene validado por get_current_user; solo lo serializamos.
    return usuario.to_dict()


@router.get("/usuarios")
def listar_usuarios(
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    """
    Lista todos los usuarios registrados.

    Parámetros:
        _: Dependencia que exige rol administrador.
        db: Sesión de base de datos.

    Respuesta:
        Lista de diccionarios, uno por usuario.

    Nivel de acceso:
        Solo administradores.
    """
    # Transformamos cada entidad Usuario a un diccionario plano para la API.
    return [
        u.to_dict()
        for u in AuthService(SQLAlchemyUsuarioRepository(db), db).listar()
    ]
