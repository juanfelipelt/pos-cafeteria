from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.schemas.configuracion import LogoUpdate
from application.services.configuracion_service import ConfiguracionService
from database import get_session
from domain.entities.usuario import Usuario
from infrastructure.api.dependencies import require_admin
from infrastructure.repositories.configuracion_repository import (
    SQLAlchemyConfiguracionRepository,
)

router = APIRouter(prefix="/configuracion", tags=["configuracion"])


@router.get("")
def obtener_todas(db: Session = Depends(get_session)):
    return ConfiguracionService(SQLAlchemyConfiguracionRepository(db), db).obtener_todas()


@router.put("/logo")
def establecer_logo(
    body: LogoUpdate,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    ConfiguracionService(SQLAlchemyConfiguracionRepository(db), db).establecer(
        "logo", body.logo
    )
    return {"logo": body.logo}
