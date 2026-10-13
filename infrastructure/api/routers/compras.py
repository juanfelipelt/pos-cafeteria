"""
Router de compras.

Recurso que expone: las compras de mercancía (productos o insumos) que el
negocio registra a sus proveedores. Cada compra tiene proveedor, fecha e
items con cantidades y precios.

Prefijo base de las rutas: `/compras`

Endpoints:
- POST   /compras                    -> registra una compra.
- GET    /compras                    -> lista compras (con filtro opcional por fechas).
- GET    /compras/{id}               -> obtiene una compra por id.
- PUT    /compras/{id}               -> actualiza una compra (solo admin).
- POST   /compras/{id}/anular        -> anula una compra (solo admin).
- DELETE /compras/{id}               -> elimina una compra (solo admin).
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.schemas.compra import CompraCreate
from application.services.compra_service import CompraService
from database import get_session
from domain.entities.usuario import Usuario
from infrastructure.api.dependencies import get_current_user, require_admin
from infrastructure.repositories.compra_repository import SQLAlchemyCompraRepository
from infrastructure.repositories.insumo_repository import (
    SQLAlchemyInsumoRepository,
)
from infrastructure.repositories.producto_repository import (
    SQLAlchemyProductoRepository,
)

# Router con prefijo "/compras".
router = APIRouter(prefix="/compras", tags=["compras"])


def _build_service(db: Session) -> CompraService:
    """
    Función auxiliar que arma el servicio de compras.

    Las compras afectan tanto a productos como a insumos (porque una compra
    puede aumentar el stock de cualquiera de los dos), por eso el servicio
    necesita varios repositorios. Centralizar su construcción aquí evita
    repetir el mismo código en cada endpoint.

    Parámetros:
        db: Sesión de base de datos.

    Respuesta:
        Una instancia lista de `CompraService`.
    """
    return CompraService(
        SQLAlchemyCompraRepository(db),
        SQLAlchemyProductoRepository(db),
        SQLAlchemyInsumoRepository(db),
        db,
    )


@router.post("")
def crear(
    body: CompraCreate,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    """
    Registra una nueva compra a un proveedor.

    Parámetros:
        body: Proveedor y lista de items (tipo, producto/insumo, cantidad,
              precio unitario).
        db: Sesión de base de datos.
        _: Exige usuario autenticado.

    Respuesta:
        La compra creada como dict.

    Nivel de acceso:
        Usuario autenticado.
    """
    # Convertimos cada item del esquema a un diccionario simple que el
    # servicio entiende, sin acoplarnos a la clase del esquema en la lógica.
    items = [
        {
            "tipo": i.tipo,
            "producto_id": i.producto_id,
            "insumo_id": i.insumo_id,
            "cantidad": i.cantidad,
            "precio_unitario": i.precio_unitario,
        }
        for i in body.items
    ]
    return _build_service(db).crear(body.proveedor_id, items).to_dict()


@router.get("")
def listar(
    desde: datetime | None = None,
    hasta: datetime | None = None,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    """
    Lista compras, opcionalmente dentro de un rango de fechas.

    Parámetros:
        desde: Fecha/hora inicial del filtro (opcional).
        hasta: Fecha/hora final del filtro (opcional).
        db: Sesión de base de datos.
        _: Exige usuario autenticado.

    Respuesta:
        Lista de compras como dict.

    Nivel de acceso:
        Usuario autenticado.
    """
    # Si no se envían fechas, el servicio devuelve todas las compras.
    return [c.to_dict() for c in _build_service(db).listar(desde, hasta)]


@router.get("/{compra_id}")
def obtener(
    compra_id: str,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    """
    Obtiene una compra por su identificador.

    Parámetros:
        compra_id: Id de la compra.
        db: Sesión de base de datos.
        _: Exige usuario autenticado.

    Respuesta:
        La compra como dict.

    Nivel de acceso:
        Usuario autenticado.
    """
    return _build_service(db).obtener(compra_id).to_dict()


@router.put("/{compra_id}")
def actualizar(
    compra_id: str,
    body: CompraCreate,
    _=Depends(require_admin),
    db: Session = Depends(get_session),
):
    """
    Actualiza por completo una compra (proveedor e items).

    Parámetros:
        compra_id: Id de la compra a modificar.
        body: Nuevos datos (proveedor e items).
        _: Exige rol administrador.
        db: Sesión de base de datos.

    Respuesta:
        La compra actualizada como dict.

    Nivel de acceso:
        Solo administradores.
    """
    # Igual que en crear, normalizamos los items a diccionarios.
    items = [
        {
            "tipo": i.tipo,
            "producto_id": i.producto_id,
            "insumo_id": i.insumo_id,
            "cantidad": i.cantidad,
            "precio_unitario": i.precio_unitario,
        }
        for i in body.items
    ]
    return _build_service(db).actualizar(
        compra_id, body.proveedor_id, items
    ).to_dict()


@router.post("/{compra_id}/anular")
def anular(
    compra_id: str,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    """
    Anula una compra (normalmente revirtiendo su efecto en el stock).

    Parámetros:
        compra_id: Id de la compra a anular.
        _: Exige rol administrador.
        db: Sesión de base de datos.

    Respuesta:
        La compra anulada como dict.

    Nivel de acceso:
        Solo administradores.
    """
    return _build_service(db).anular(compra_id).to_dict()


@router.delete("/{compra_id}")
def eliminar(
    compra_id: str,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    """
    Elimina definitivamente una compra.

    Parámetros:
        compra_id: Id de la compra a eliminar.
        _: Exige rol administrador.
        db: Sesión de base de datos.

    Respuesta:
        Mensaje de confirmación.

    Nivel de acceso:
        Solo administradores.
    """
    _build_service(db).eliminar(compra_id)
    return {"detail": "Compra eliminada."}
