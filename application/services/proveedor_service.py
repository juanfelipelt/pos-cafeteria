"""Servicio de proveedores (caso de uso: "Gestión de proveedores").

¿Qué resuelve?
- Administrar los datos de los proveedores a los que se les compra:
  contacto, teléfono, email, dirección e identificación.
- Impedir borrar un proveedor que ya tenga compras registradas.

¿Cómo usa los repositorios?
- ``ProveedorRepository``: CRUD de proveedores.
- ``CompraRepository``: se consulta ``has_for_proveedor`` para saber si el
  proveedor tiene compras y así proteger la integridad histórica.
- ``Session``: confirma los cambios.
"""

from sqlalchemy.orm import Session

from application.utils import new_id
from domain.entities.proveedor import Proveedor
from domain.exceptions import ConflictError, NotFoundError
from domain.repositories.compra_repository import CompraRepository
from domain.repositories.proveedor_repository import ProveedorRepository


class ProveedorService:
    """Gestiona el catálogo de proveedores."""

    def __init__(
        self,
        proveedores: ProveedorRepository,
        compras: CompraRepository,
        session: Session,
    ) -> None:
        """Guarda las dependencias del servicio.

        Parámetros:
            proveedores: repositorio de proveedores.
            compras: repositorio de compras (para validar dependencias).
            session: sesión de SQLAlchemy para confirmar cambios.
        """
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
        tipo_identificacion: str = "",
        identificacion: str = "",
    ) -> Proveedor:
        """Crea un proveedor nuevo.

        Parámetros:
            nombre: razón social o nombre del proveedor.
            contacto: persona de contacto.
            telefono: teléfono de contacto.
            email: correo electrónico (opcional).
            direccion: dirección (opcional).
            tipo_identificacion: tipo de documento (opcional).
            identificacion: número de documento (opcional).

        Retorna:
            El proveedor creado y confirmado.
        """
        proveedor = Proveedor(
            id=new_id(),
            nombre=nombre,
            contacto=contacto,
            telefono=telefono,
            email=email,
            direccion=direccion,
            tipo_identificacion=tipo_identificacion,
            identificacion=identificacion,
        )
        self.proveedores.add(proveedor)
        self.session.commit()
        return proveedor

    def listar(
        self, filtro: str | None = None, solo_activos: bool = False
    ) -> list[Proveedor]:
        """Lista proveedores con filtro de texto y estado.

        Parámetros:
            filtro: texto a buscar (opcional).
            solo_activos: si es ``True``, excluye los inactivos.

        Retorna:
            Lista de proveedores que cumplen los criterios.
        """
        return self.proveedores.list(filtro, solo_activos)

    def obtener(self, proveedor_id: str) -> Proveedor:
        """Busca un proveedor por id.

        Parámetros:
            proveedor_id: identificador del proveedor.

        Retorna:
            El proveedor encontrado.

        Lanza:
            NotFoundError: si no existe.
        """
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
        tipo_identificacion: str | None = None,
        identificacion: str | None = None,
    ) -> Proveedor:
        """Actualiza los campos enviados de un proveedor.

        Solo se modifican los valores distintos de ``None``.

        Parámetros:
            proveedor_id: id del proveedor a modificar.
            nombre, contacto, telefono, email, direccion,
            tipo_identificacion, identificacion: nuevos valores (opcionales).

        Retorna:
            El proveedor actualizado.

        Lanza:
            NotFoundError: si no existe.
        """
        proveedor = self.obtener(proveedor_id)
        # Cada campo se cambia solo si fue enviado (no es None).
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
        if tipo_identificacion is not None:
            proveedor.cambiar_tipo_identificacion(tipo_identificacion)
        if identificacion is not None:
            proveedor.cambiar_identificacion(identificacion)
        self.proveedores.update(proveedor)
        self.session.commit()
        return proveedor

    def cambiar_estado(self, proveedor_id: str, estado: bool) -> Proveedor:
        """Activa o desactiva un proveedor.

        Parámetros:
            proveedor_id: id del proveedor.
            estado: ``True`` para activar, ``False`` para desactivar.

        Retorna:
            El proveedor con su nuevo estado.

        Lanza:
            NotFoundError: si no existe.
        """
        proveedor = self.obtener(proveedor_id)
        if estado:
            proveedor.activar()
        else:
            proveedor.desactivar()
        self.proveedores.update(proveedor)
        self.session.commit()
        return proveedor

    def eliminar(self, proveedor_id: str) -> None:
        """Elimina un proveedor si no tiene compras registradas.

        Parámetros:
            proveedor_id: id del proveedor a eliminar.

        Lanza:
            NotFoundError: si no existe.
            ConflictError: si el proveedor tiene compras.
        """
        proveedor = self.obtener(proveedor_id)
        # Integridad: no se borra un proveedor con historial de compras.
        if self.compras.has_for_proveedor(proveedor_id):
            raise ConflictError(
                "No se puede eliminar: el proveedor tiene compras registradas."
            )
        self.proveedores.delete(proveedor.id)
        self.session.commit()
