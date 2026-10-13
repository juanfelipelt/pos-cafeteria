"""
Router de ventas.

Recurso que expone: las ventas realizadas (con sus items y pagos). Al crear
una venta se descuenta stock según las recetas; un pago puede ser parcial, por
lo que existe un endpoint para registrar pagos adicionales.

Prefijo base de las rutas: `/ventas`

Endpoints:
- POST   /ventas                -> registra una venta.
- GET    /ventas                -> lista ventas (filtro por fechas).
- GET    /ventas/{id}           -> obtiene una venta por id.
- POST   /ventas/{id}/pagos     -> registra un pago sobre la venta.
- POST   /ventas/{id}/anular    -> anula una venta (solo admin).
- DELETE /ventas/{id}           -> elimina una venta (solo admin).
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.schemas.venta import PagoCreate, VentaCreate
from application.services.venta_service import VentaService
from database import get_session
from domain.entities.usuario import Usuario
from infrastructure.api.dependencies import get_current_user, require_admin
from infrastructure.repositories.insumo_repository import (
    SQLAlchemyInsumoRepository,
)
from infrastructure.repositories.producto_repository import (
    SQLAlchemyProductoRepository,
)
from infrastructure.repositories.receta_repository import (
    SQLAlchemyRecetaRepository,
)
from infrastructure.repositories.venta_repository import SQLAlchemyVentaRepository

# Router con prefijo "/ventas".
router = APIRouter(prefix="/ventas", tags=["ventas"])


def _build_service(db: Session) -> VentaService:
    """
    Función auxiliar que arma el servicio de ventas.

    Una venta afecta a productos, insumos (por las recetas) y a la propia
    venta, por eso el servicio recibe varios repositorios.

    Parámetros:
        db: Sesión de base de datos.

    Respuesta:
        Una instancia lista de `VentaService`.
    """
    return VentaService(
        SQLAlchemyVentaRepository(db),
        SQLAlchemyProductoRepository(db),
        SQLAlchemyInsumoRepository(db),
        SQLAlchemyRecetaRepository(db),
        db,
    )


@router.post("")
def crear(
    body: VentaCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """
    Registra una nueva venta.

    Parámetros:
        body: Items vendidos (producto y cantidad) y pagos.
        usuario: Usuario autenticado que registra la venta.
        db: Sesión de base de datos.

    Respuesta:
        La venta creada como dict.

    Nivel de acceso:
        Usuario autenticado.
    """
    # Convertimos los items a diccionarios simples.
    items = [{"producto_id": i.producto_id, "cantidad": i.cantidad} for i in body.items]
    # Convertimos los pagos; usamos `.value` para guardar el valor del enum
    # (por ejemplo "efectivo") y no el objeto enum completo.
    pagos = [
        {"monto": p.monto, "metodo": p.metodo.value, "referencia": p.referencia}
        for p in body.pagos
    ]
    # Se registra la venta a nombre del usuario conectado.
    return _build_service(db).crear(items, pagos, usuario.id).to_dict()


@router.get("")
def listar(
    desde: datetime | None = None,
    hasta: datetime | None = None,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    """
    Lista las ventas, opcionalmente dentro de un rango de fechas.

    Parámetros:
        desde: Fecha/hora inicial del filtro (opcional).
        hasta: Fecha/hora final del filtro (opcional).
        db: Sesión de base de datos.
        _: Exige usuario autenticado.

    Respuesta:
        Lista de ventas como dict.

    Nivel de acceso:
        Usuario autenticado.
    """
    return [v.to_dict() for v in _build_service(db).listar(desde, hasta)]


@router.get("/{venta_id}")
def obtener(
    venta_id: str,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    """
    Obtiene una venta por su identificador.

    Parámetros:
        venta_id: Id de la venta.
        db: Sesión de base de datos.
        _: Exige usuario autenticado.

    Respuesta:
        La venta como dict (con items y pagos).

    Nivel de acceso:
        Usuario autenticado.
    """
    return _build_service(db).obtener(venta_id).to_dict()


@router.post("/{venta_id}/pagos")
def registrar_pago(
    venta_id: str,
    body: PagoCreate,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    """
    Registra un pago adicional sobre una venta existente.

    Sirve para ventas a crédito o pagos en varias partes.

    Parámetros:
        venta_id: Id de la venta a la que se abona.
        body: Datos del pago (monto, método y referencia).
        db: Sesión de base de datos.
        _: Exige usuario autenticado.

    Respuesta:
        La venta actualizada como dict.

    Nivel de acceso:
        Usuario autenticado.
    """
    return _build_service(db).registrar_pago(
        venta_id, body.monto, body.metodo.value, body.referencia
    ).to_dict()


@router.post("/{venta_id}/anular")
def anular(
    venta_id: str,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    """
    Anula una venta (normalmente devolviendo el stock descontado).

    Parámetros:
        venta_id: Id de la venta a anular.
        _: Exige rol administrador.
        db: Sesión de base de datos.

    Respuesta:
        La venta anulada como dict.

    Nivel de acceso:
        Solo administradores.
    """
    return _build_service(db).anular(venta_id).to_dict()


@router.delete("/{venta_id}")
def eliminar(
    venta_id: str,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    """
    Elimina definitivamente una venta.

    Parámetros:
        venta_id: Id de la venta a eliminar.
        _: Exige rol administrador.
        db: Sesión de base de datos.

    Respuesta:
        Mensaje de confirmación.

    Nivel de acceso:
        Solo administradores.
    """
    _build_service(db).eliminar(venta_id)
    return {"detail": "Venta eliminada."}
