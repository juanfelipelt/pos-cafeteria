from sqlalchemy.orm import Session

from application.utils import new_id
from domain.entities.insumo import Insumo
from domain.exceptions import ConflictError, NotFoundError
from domain.repositories.insumo_repository import InsumoRepository
from domain.repositories.receta_repository import RecetaRepository


class InsumoService:
    def __init__(
        self,
        insumos: InsumoRepository,
        recetas: RecetaRepository,
        session: Session,
    ) -> None:
        self.insumos = insumos
        self.recetas = recetas
        self.session = session

    def crear(
        self,
        nombre: str,
        unidad: str,
        stock: float = 0.0,
        costo_unitario: float = 0.0,
        proveedor_id: str | None = None,
    ) -> Insumo:
        insumo = Insumo(
            id=new_id(),
            nombre=nombre,
            unidad=unidad,
            stock=stock,
            costo_unitario=costo_unitario,
            proveedor_id=proveedor_id,
        )
        self.insumos.add(insumo)
        self.session.commit()
        return insumo

    def listar(
        self, filtro: str | None = None, solo_activos: bool = False
    ) -> list[Insumo]:
        return self.insumos.list(filtro, solo_activos)

    def obtener(self, insumo_id: str) -> Insumo:
        insumo = self.insumos.get(insumo_id)
        if insumo is None:
            raise NotFoundError("Insumo no encontrado.")
        return insumo

    def actualizar(
        self,
        insumo_id: str,
        nombre: str | None = None,
        unidad: str | None = None,
        stock: float | None = None,
        costo_unitario: float | None = None,
        proveedor_id: str | None = None,
    ) -> Insumo:
        insumo = self.obtener(insumo_id)
        if nombre is not None:
            insumo.cambiar_nombre(nombre)
        if unidad is not None:
            insumo.cambiar_unidad(unidad)
        if stock is not None:
            if stock < 0:
                raise ValueError("El stock no puede ser negativo.")
            insumo.stock = stock
        if costo_unitario is not None:
            if costo_unitario < 0:
                raise ValueError("El costo no puede ser negativo.")
            insumo.costo_unitario = costo_unitario
        if proveedor_id is not None:
            insumo.cambiar_proveedor_id(proveedor_id)
        self.insumos.update(insumo)
        self.session.commit()
        return insumo

    def cambiar_estado(self, insumo_id: str, estado: bool) -> Insumo:
        insumo = self.obtener(insumo_id)
        if estado:
            insumo.activar()
        else:
            insumo.desactivar()
        self.insumos.update(insumo)
        self.session.commit()
        return insumo

    def eliminar(self, insumo_id: str) -> None:
        self.obtener(insumo_id)
        if self.recetas.has_for_insumo(insumo_id):
            raise ConflictError(
                "No se puede eliminar: el insumo está en la receta de un producto."
            )
        self.insumos.delete(insumo_id)
        self.session.commit()
