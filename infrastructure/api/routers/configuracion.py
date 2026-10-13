"""
Router de configuración del sistema.

Recurso que expone: pares clave/valor de configuración general del negocio
(por ejemplo, el logo, el nombre del establecimiento, etc.). Es como un
"tablero de ajustes" que el administrador puede cambiar sin tocar código.

Prefijo base de las rutas: `/configuracion`

Endpoints:
- GET /configuracion        -> devuelve toda la configuración.
- PUT /configuracion/logo   -> guarda el logo (solo admin).
- PUT /configuracion/{clave}-> guarda el valor de una clave (solo admin).

Nota: la ruta `/logo` se declara ANTES que `/{clave}` para que FastAPI no
interprete "logo" como el comodín `{clave}`.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.schemas.configuracion import ConfiguracionUpdate, LogoUpdate
from application.services.configuracion_service import ConfiguracionService
from database import get_session
from domain.entities.usuario import Usuario
from infrastructure.api.dependencies import require_admin
from infrastructure.repositories.configuracion_repository import (
    SQLAlchemyConfiguracionRepository,
)

# Router con prefijo "/configuracion".
router = APIRouter(prefix="/configuracion", tags=["configuracion"])


@router.get("")
def obtener_todas(db: Session = Depends(get_session)):
    """
    Devuelve toda la configuración almacenada.

    Parámetros:
        db: Sesión de base de datos.

    Respuesta:
        Diccionario/estructura con todas las claves y sus valores.

    Nivel de acceso:
        Público (la configuración básica se consulta sin token).
    """
    # El servicio recolecta todas las claves configuradas en la base de datos.
    return ConfiguracionService(SQLAlchemyConfiguracionRepository(db), db).obtener_todas()


@router.put("/logo")
def establecer_logo(
    body: LogoUpdate,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    """
    Establece el logo del negocio.

    Parámetros:
        body: Contiene el logo (por ejemplo, una URL o datos de la imagen).
        _: Exige rol administrador.
        db: Sesión de base de datos.

    Respuesta:
        Diccionario con la clave "logo" y su nuevo valor.

    Nivel de acceso:
        Solo administradores.
    """
    # Guardamos el logo bajo la clave fija "logo".
    ConfiguracionService(SQLAlchemyConfiguracionRepository(db), db).establecer(
        "logo", body.logo
    )
    return {"logo": body.logo}


@router.put("/{clave}")
def establecer_valor(
    clave: str,
    body: ConfiguracionUpdate,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    """
    Establece el valor de una clave de configuración arbitraria.

    Parámetros:
        clave: Nombre de la configuración (parte de la URL).
        body: Nuevo valor para esa clave.
        _: Exige rol administrador.
        db: Sesión de base de datos.

    Respuesta:
        Diccionario con la clave enviada y su nuevo valor.

    Nivel de acceso:
        Solo administradores.
    """
    # Upsert: crea la clave si no existe o actualiza su valor si ya existe.
    ConfiguracionService(SQLAlchemyConfiguracionRepository(db), db).establecer(
        clave, body.valor
    )
    return {clave: body.valor}
