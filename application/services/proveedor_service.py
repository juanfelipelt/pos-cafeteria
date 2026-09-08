from sqlalchemy.orm import Session

from application.utils import new_id
from domain.entities.proveedor import Proveedor
from domain.exceptions import ConflictError, NotFoundError
from domain.repositories.compra_repository import CompraRepository
from domain.repositories.proveedor_repository import ProveedorRepository


class ProveedorService:
    def __init__(
        self,
        proveedores: ProveedorRepository,
        compras: CompraRepository,
        session: Session,
    ) -> None:
        self.proveedores = proveedores
        self.compras = compras
        self.session = session

    def crear(
        self,
        nombre: str,
        contacto: str,
        telefono: str,
        email: str = "",
        direccion: str = "",
    ) -> Proveedor:
        proveedor = Proveedor(
            id=new_id(),
            nombre=nombre,
            contacto=contacto,
            telefono=telefono,
            email=email,
            direccion=direccion,
        )
        self.proveedores.add(proveedor)
        self.session.commit()
        return proveedor

    def listar(
        self, filtro: str | None = None, solo_activos: bool = False
    ) -> list[Proveedor]:
        return self.proveedores.list(filtro, solo_activos)

    def obtener(self, proveedor_id: str) -> Proveedor:
        proveedor = self.proveedores.get(proveedor_id)
        if proveedor is None:
            raise NotFoundError("Proveedor no encontrado.")
        return proveedor

    def actualizar(
        self,
        proveedor_id: str,
        nombre: str | None = None,
        contacto: str | None = None,
        telefono: str | None = None,
        email: str | None = None,
        direccion: str | None = None,
    ) -> Proveedor:
        proveedor = self.obtener(proveedor_id)
        if nombre is not None:
            proveedor.cambiar_nombre(nombre)
        if contacto is not None:
            proveedor.cambiar_contacto(contacto)
        if telefono is not None:
            proveedor.cambiar_telefono(telefono)
        if email is not None:
            proveedor.cambiar_email(email)
        if direccion is not None:
            proveedor.cambiar_direccion(direccion)
        self.proveedores.update(proveedor)
        self.session.commit()
        return proveedor

    def cambiar_estado(self, proveedor_id: str, estado: bool) -> Proveedor:
        proveedor = self.obtener(proveedor_id)
        if estado:
            proveedor.activar()
        else:
            proveedor.desactivar()
        self.proveedores.update(proveedor)
        self.session.commit()
        return proveedor

    def eliminar(self, proveedor_id: str) -> None:
        proveedor = self.obtener(proveedor_id)
        if self.compras.has_for_proveedor(proveedor_id):
            raise ConflictError(
                "No se puede eliminar: el proveedor tiene compras registradas."
            )
        self.proveedores.delete(proveedor.id)
        self.session.commit()
