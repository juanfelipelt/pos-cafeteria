"""Repositorio SQLAlchemy para los productos.

Implementa `ProductoRepository` del dominio sobre la tabla `productos`.
Permite buscar, filtrar (por nombre, categoría y estado) y administrar
productos del catálogo.
"""

from __future__ import annotations
# `func` para ordenar alfabéticamente sin distinguir mayúsculas.
from sqlalchemy import func
from sqlalchemy.orm import Session

from domain.entities.producto import Producto
from domain.repositories.producto_repository import ProductoRepository
from infrastructure.models.producto import ProductoModel


def _to_entity(m: ProductoModel) -> Producto:
    """Convierte un modelo ORM `ProductoModel` en la entidad `Producto`."""
    return Producto(
        id=m.id,
        nombre=m.nombre,
        descripcion=m.descripcion,
        categoria_id=m.categoria_id,
        imagen=m.imagen,
        precio=m.precio,
        stock=m.stock,
        estado=m.estado,
        tipo=m.tipo,
        costo=m.costo,
    )


class SQLAlchemyProductoRepository(ProductoRepository):
    """Implementación concreta de `ProductoRepository` con SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id: str) -> Producto | None:
        """Busca un producto por id. None si no existe."""
        m = self.session.get(ProductoModel, id)
        return _to_entity(m) if m else None

    def list(
        self,
        filtro: str | None = None,
        categoria_id: str | None = None,
        solo_activos: bool = False,
    ) -> list[Producto]:
        """Lista productos con filtros opcionales.

        - `filtro`: texto que debe aparecer en el nombre.
        - `categoria_id`: solo productos de esa categoría.
        - `solo_activos`: si es True, solo productos activos.
        """
        q = self.session.query(ProductoModel)
        if filtro:
            # Búsqueda parcial por nombre, sin importar mayúsculas.
            q = q.filter(ProductoModel.nombre.ilike(f"%{filtro}%"))
        if categoria_id:
            q = q.filter(ProductoModel.categoria_id == categoria_id)
        if solo_activos:
            q = q.filter(ProductoModel.estado.is_(True))
        # Orden alfabético estable (minúscula y luego el nombre original).
        q = q.order_by(func.lower(ProductoModel.nombre).asc(), ProductoModel.nombre.asc())
        return [_to_entity(m) for m in q.all()]

    def add(self, producto: Producto) -> Producto:
        """Registra un nuevo producto."""
        m = ProductoModel(
            id=producto.id,
            nombre=producto.nombre,
            descripcion=producto.descripcion,
            categoria_id=producto.categoria_id,
            imagen=producto.imagen,
            precio=producto.precio,
            stock=producto.stock,
            estado=producto.estado,
            tipo=producto.tipo,
            costo=producto.costo,
        )
        self.session.add(m)
        self.session.flush()
        return producto

    def update(self, producto: Producto) -> Producto:
        """Actualiza un producto existente con los datos de la entidad."""
        m = self.session.get(ProductoModel, producto.id)
        m.nombre = producto.nombre
        m.descripcion = producto.descripcion
        m.categoria_id = producto.categoria_id
        m.imagen = producto.imagen
        m.precio = producto.precio
        m.stock = producto.stock
        m.estado = producto.estado
        m.tipo = producto.tipo
        m.costo = producto.costo
        self.session.flush()
        return producto
