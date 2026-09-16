from sqlalchemy import func
from sqlalchemy.orm import Session

from domain.entities.insumo import Insumo
from domain.repositories.insumo_repository import InsumoRepository
from infrastructure.models.insumo import InsumoModel


def _to_entity(m: InsumoModel) -> Insumo:
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
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id: str) -> Insumo | None:
        m = self.session.get(InsumoModel, id)
        return _to_entity(m) if m else None

    def list(
        self,
        filtro: str | None = None,
        solo_activos: bool = False,
    ) -> list[Insumo]:
        q = self.session.query(InsumoModel)
        if filtro:
            q = q.filter(InsumoModel.nombre.ilike(f"%{filtro}%"))
        if solo_activos:
            q = q.filter(InsumoModel.estado.is_(True))
        q = q.order_by(func.lower(InsumoModel.nombre).asc(), InsumoModel.nombre.asc())
        return [_to_entity(m) for m in q.all()]

    def add(self, insumo: Insumo) -> Insumo:
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
        m = self.session.get(InsumoModel, id)
        if m is not None:
            self.session.delete(m)
            self.session.flush()
