from sqlalchemy.orm import Session

from domain.entities.proveedor import Proveedor
from domain.repositories.proveedor_repository import ProveedorRepository
from infrastructure.models.proveedor import ProveedorModel


def _to_entity(m: ProveedorModel) -> Proveedor:
    return Proveedor(
        id=m.id,
        nombre=m.nombre,
        contacto=m.contacto,
        telefono=m.telefono,
        email=m.email,
        direccion=m.direccion,
        estado=m.estado,
    )


class SQLAlchemyProveedorRepository(ProveedorRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id: str) -> Proveedor | None:
        m = self.session.get(ProveedorModel, id)
        return _to_entity(m) if m else None

    def list(
        self, filtro: str | None = None, solo_activos: bool = False
    ) -> list[Proveedor]:
        q = self.session.query(ProveedorModel)
        if filtro:
            q = q.filter(ProveedorModel.nombre.ilike(f"%{filtro}%"))
        if solo_activos:
            q = q.filter(ProveedorModel.estado.is_(True))
        return [_to_entity(m) for m in q.all()]

    def add(self, proveedor: Proveedor) -> Proveedor:
        m = ProveedorModel(
            id=proveedor.id,
            nombre=proveedor.nombre,
            contacto=proveedor.contacto,
            telefono=proveedor.telefono,
            email=proveedor.email,
            direccion=proveedor.direccion,
            estado=proveedor.estado,
        )
        self.session.add(m)
        self.session.flush()
        return proveedor

    def update(self, proveedor: Proveedor) -> Proveedor:
        m = self.session.get(ProveedorModel, proveedor.id)
        m.nombre = proveedor.nombre
        m.contacto = proveedor.contacto
        m.telefono = proveedor.telefono
        m.email = proveedor.email
        m.direccion = proveedor.direccion
        m.estado = proveedor.estado
        self.session.flush()
        return proveedor

    def delete(self, id: str) -> None:
        m = self.session.get(ProveedorModel, id)
        if m is not None:
            self.session.delete(m)
            self.session.flush()
