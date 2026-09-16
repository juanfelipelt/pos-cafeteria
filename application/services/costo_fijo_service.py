from sqlalchemy.orm import Session

from application.utils import new_id
from domain.entities.costo_fijo import CostoFijo
from domain.exceptions import NotFoundError
from domain.repositories.costo_fijo_repository import CostoFijoRepository


class CostoFijoService:
    def __init__(self, costos: CostoFijoRepository, session: Session) -> None:
        self.costos = costos
        self.session = session

    def crear(self, nombre: str, monto: float = 0.0) -> CostoFijo:
        costo = CostoFijo(id=new_id(), nombre=nombre, monto=monto)
        self.costos.add(costo)
        self.session.commit()
        return costo

    def listar(self, solo_activos: bool = False) -> list[CostoFijo]:
        return self.costos.list(solo_activos)

    def obtener(self, costo_id: str) -> CostoFijo:
        costo = self.costos.get(costo_id)
        if costo is None:
            raise NotFoundError("Costo fijo no encontrado.")
        return costo

    def actualizar(
        self,
        costo_id: str,
        nombre: str | None = None,
        monto: float | None = None,
        activo: bool | None = None,
    ) -> CostoFijo:
        costo = self.obtener(costo_id)
        if nombre is not None:
            costo.cambiar_nombre(nombre)
        if monto is not None:
            costo.cambiar_monto(monto)
        if activo is not None:
            if activo:
                costo.activar()
            else:
                costo.desactivar()
        self.costos.update(costo)
        self.session.commit()
        return costo

    def eliminar(self, costo_id: str) -> None:
        self.obtener(costo_id)
        self.costos.delete(costo_id)
        self.session.commit()
