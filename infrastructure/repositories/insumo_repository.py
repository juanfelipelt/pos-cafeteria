"""Repositorio SQLAlchemy para los insumos.

Implementa `InsumoRepository` del dominio sobre la tabla `insumos`. Permite
buscar, listar (con filtros), crear, actualizar y eliminar insumos.
"""

from __future__ import annotations
# `func` para ordenar alfabéticamente sin distinguir mayúsculas.
from sqlalchemy import func
from sqlalchemy.orm import Session

from domain.entities.insumo import Insumo
from domain.repositories.insumo_repository import InsumoRepository
from infrastructure.models.insumo import InsumoModel


def _to_entity(m: InsumoModel) -> Insumo:
    """Convierte un modelo ORM `InsumoModel` en la entidad `Insumo`."""
    return Insumo(
        id=m.id,
        nombre=m.nombre,
        unidad=m.unidad,
        stock=m.stock,
        costo_unitario=m.costo_unitario,
        proveedor_id=m.proveedor_id,
        estado=m.estado,
    )


class SQLAlchemyInsumoRepository(InsumoRepository):
    """Implementación concreta de `InsumoRepository` con SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id: str) -> Insumo | None:
        """Busca un insumo por id. None si no existe."""
        m = self.session.get(InsumoModel, id)
        return _to_entity(m) if m else None

    def list(
        self,
        filtro: str | None = None,
        solo_activos: bool = False,
    ) -> list[Insumo]:
        """Lista insumos con filtros opcionales.

        - `filtro`: texto que debe aparecer en el nombre (búsqueda parcial).
        - `solo_activos`: si es True, solo insumos con estado activo.
        """
        q = self.session.query(InsumoModel)
        if filtro:
            # ilike = búsqueda "contiene" sin distinguir mayúsculas/minúsculas.
            q = q.filter(InsumoModel.nombre.ilike(f"%{filtro}%"))
        if solo_activos:
            q = q.filter(InsumoModel.estado.is_(True))
        # Orden alfabético estable: primero por minúscula, luego por el nombre tal cual.
        q = q.order_by(func.lower(InsumoModel.nombre).asc(), InsumoModel.nombre.asc())
        return [_to_entity(m) for m in q.all()]

    def add(self, insumo: Insumo) -> Insumo:
        """Registra un nuevo insumo."""
        m = InsumoModel(
            id=insumo.id,
            nombre=insumo.nombre,
            unidad=insumo.unidad,
            stock=insumo.stock,
            costo_unitario=insumo.costo_unitario,
            proveedor_id=insumo.proveedor_id,
            estado=insumo.estado,
        )
        self.session.add(m)
        self.session.flush()
        return insumo

    def update(self, insumo: Insumo) -> Insumo:
        """Actualiza un insumo existente con los datos de la entidad."""
        m = self.session.get(InsumoModel, insumo.id)
        m.nombre = insumo.nombre
        m.unidad = insumo.unidad
        m.stock = insumo.stock
        m.costo_unitario = insumo.costo_unitario
        m.proveedor_id = insumo.proveedor_id
        m.estado = insumo.estado
        self.session.flush()
        return insumo

    def delete(self, id: str) -> None:
        """Elimina un insumo si existe."""
        m = self.session.get(InsumoModel, id)
        if m is not None:
            self.session.delete(m)
            self.session.flush()
