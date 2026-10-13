"""Repositorio SQLAlchemy para los costos fijos.

Implementa `CostoFijoRepository` del dominio sobre la tabla `costos_fijos`.
Permite crear, listar, actualizar y eliminar gastos fijos del negocio.
"""

from __future__ import annotations
# `func` se usa para ordenar ignorando mayúsculas/minúsculas (func.lower).
from sqlalchemy import func
from sqlalchemy.orm import Session

from domain.entities.costo_fijo import CostoFijo
from domain.repositories.costo_fijo_repository import CostoFijoRepository
from infrastructure.models.costo_fijo import CostoFijoModel


def _to_entity(m: CostoFijoModel) -> CostoFijo:
    """Convierte un modelo ORM `CostoFijoModel` en la entidad `CostoFijo`."""
    return CostoFijo(
        id=m.id,
        nombre=m.nombre,
        monto=m.monto,
        activo=m.activo,
    )


class SQLAlchemyCostoFijoRepository(CostoFijoRepository):
    """Implementación concreta de `CostoFijoRepository` con SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id: str) -> CostoFijo | None:
        """Busca un costo fijo por id. None si no existe."""
        m = self.session.get(CostoFijoModel, id)
        return _to_entity(m) if m else None

    def list(self, solo_activos: bool = False) -> list[CostoFijo]:
        """Lista los costos fijos ordenados alfabéticamente por nombre.

        Si `solo_activos` es True, excluye los que están desactivados.
        """
        q = self.session.query(CostoFijoModel)
        if solo_activos:
            q = q.filter(CostoFijoModel.activo.is_(True))
        # Orden insensible a mayúsculas para que "arriendo" y "Arriendo" queden juntos.
        q = q.order_by(func.lower(CostoFijoModel.nombre).asc())
        return [_to_entity(m) for m in q.all()]

    def add(self, costo: CostoFijo) -> CostoFijo:
        """Registra un nuevo costo fijo."""
        m = CostoFijoModel(
            id=costo.id,
            nombre=costo.nombre,
            monto=costo.monto,
            activo=costo.activo,
        )
        self.session.add(m)
        self.session.flush()
        return costo

    def update(self, costo: CostoFijo) -> CostoFijo:
        """Actualiza un costo fijo existente."""
        m = self.session.get(CostoFijoModel, costo.id)
        m.nombre = costo.nombre
        m.monto = costo.monto
        m.activo = costo.activo
        self.session.flush()
        return costo

    def delete(self, id: str) -> None:
        """Elimina un costo fijo si existe."""
        m = self.session.get(CostoFijoModel, id)
        if m is not None:
            self.session.delete(m)
            self.session.flush()
