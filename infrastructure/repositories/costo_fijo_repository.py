from sqlalchemy import func
from sqlalchemy.orm import Session

from domain.entities.costo_fijo import CostoFijo
from domain.repositories.costo_fijo_repository import CostoFijoRepository
from infrastructure.models.costo_fijo import CostoFijoModel


def _to_entity(m: CostoFijoModel) -> CostoFijo:
    return CostoFijo(
        id=m.id,
        nombre=m.nombre,
        monto=m.monto,
        activo=m.activo,
    )


class SQLAlchemyCostoFijoRepository(CostoFijoRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id: str) -> CostoFijo | None:
        m = self.session.get(CostoFijoModel, id)
        return _to_entity(m) if m else None

    def list(self, solo_activos: bool = False) -> list[CostoFijo]:
        q = self.session.query(CostoFijoModel)
        if solo_activos:
            q = q.filter(CostoFijoModel.activo.is_(True))
        q = q.order_by(func.lower(CostoFijoModel.nombre).asc())
        return [_to_entity(m) for m in q.all()]

    def add(self, costo: CostoFijo) -> CostoFijo:
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
        m = self.session.get(CostoFijoModel, costo.id)
        m.nombre = costo.nombre
        m.monto = costo.monto
        m.activo = costo.activo
        self.session.flush()
        return costo

    def delete(self, id: str) -> None:
        m = self.session.get(CostoFijoModel, id)
        if m is not None:
            self.session.delete(m)
            self.session.flush()
