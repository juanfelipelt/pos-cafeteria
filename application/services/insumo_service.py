"""Servicio de insumos (caso de uso: "Materias primas / Insumos").

¿Qué resuelve?
- Administrar los insumos (materias primas) que se usan en las recetas:
  nombre, unidad de medida, stock, costo unitario y proveedor.
- Impedir borrar un insumo que esté siendo usado en la receta de un producto.

¿Cómo usa los repositorios?
- ``InsumoRepository``: CRUD de insumos.
- ``RecetaRepository``: se consulta ``has_for_insumo`` para saber si el
  insumo está referenciado en alguna receta.
- ``Session``: confirma los cambios.

El costo unitario de los insumos es la base del costo de los productos
preparados.
"""

from sqlalchemy.orm import Session

from application.utils import new_id
from domain.entities.insumo import Insumo
from domain.exceptions import ConflictError, NotFoundError
from domain.repositories.insumo_repository import InsumoRepository
from domain.repositories.receta_repository import RecetaRepository


class InsumoService:
    """Gestiona el inventario de insumos."""

    def __init__(
        self,
        insumos: InsumoRepository,
        recetas: RecetaRepository,
        session: Session,
    ) -> None:
        """Guarda las dependencias del servicio.

        Parámetros:
            insumos: repositorio de insumos.
            recetas: repositorio de recetas (para validar dependencias).
            session: sesión de SQLAlchemy para confirmar cambios.
        """
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
        """Crea un insumo nuevo.

        Parámetros:
            nombre: nombre del insumo.
            unidad: unidad de medida (kg, litro, unidad, etc.).
            stock: cantidad inicial disponible; por defecto 0.
            costo_unitario: costo por unidad; por defecto 0.
            proveedor_id: proveedor habitual (opcional).

        Retorna:
            El insumo creado y confirmado.
        """
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
        """Lista insumos, con filtro opcional por texto y por estado.

        Parámetros:
            filtro: texto a buscar en el nombre (opcional).
            solo_activos: si es ``True``, excluye los inactivos.

        Retorna:
            Lista de insumos que cumplen los criterios.
        """
        return self.insumos.list(filtro, solo_activos)

    def obtener(self, insumo_id: str) -> Insumo:
        """Busca un insumo por id.

        Parámetros:
            insumo_id: identificador del insumo.

        Retorna:
            El insumo encontrado.

        Lanza:
            NotFoundError: si no existe.
        """
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
        """Actualiza los campos enviados de un insumo.

        Solo se modifican los valores distintos de ``None``. El stock y el
        costo no pueden quedar en negativo.

        Parámetros:
            insumo_id: id del insumo a modificar.
            nombre: nuevo nombre (opcional).
            unidad: nueva unidad (opcional).
            stock: nuevo stock (opcional, no negativo).
            costo_unitario: nuevo costo (opcional, no negativo).
            proveedor_id: nuevo proveedor (opcional).

        Retorna:
            El insumo actualizado.

        Lanza:
            NotFoundError: si no existe.
            ValueError: si el stock o el costo son negativos.
        """
        insumo = self.obtener(insumo_id)
        if nombre is not None:
            insumo.cambiar_nombre(nombre)
        if unidad is not None:
            insumo.cambiar_unidad(unidad)
        if stock is not None:
            # Regla de negocio: el inventario no puede ser negativo.
            if stock < 0:
                raise ValueError("El stock no puede ser negativo.")
            insumo.stock = stock
        if costo_unitario is not None:
            # Regla de negocio: un costo negativo no tiene sentido.
            if costo_unitario < 0:
                raise ValueError("El costo no puede ser negativo.")
            insumo.costo_unitario = costo_unitario
        if proveedor_id is not None:
            insumo.cambiar_proveedor_id(proveedor_id)
        self.insumos.update(insumo)
        self.session.commit()
        return insumo

    def cambiar_estado(self, insumo_id: str, estado: bool) -> Insumo:
        """Activa o desactiva un insumo.

        Parámetros:
            insumo_id: id del insumo.
            estado: ``True`` para activar, ``False`` para desactivar.

        Retorna:
            El insumo con su nuevo estado.

        Lanza:
            NotFoundError: si no existe.
        """
        insumo = self.obtener(insumo_id)
        if estado:
            insumo.activar()
        else:
            insumo.desactivar()
        self.insumos.update(insumo)
        self.session.commit()
        return insumo

    def eliminar(self, insumo_id: str) -> None:
        """Elimina un insumo si no está usado en ninguna receta.

        Parámetros:
            insumo_id: id del insumo a eliminar.

        Lanza:
            NotFoundError: si no existe.
            ConflictError: si el insumo está en la receta de un producto.
        """
        self.obtener(insumo_id)
        # Integridad de negocio: no se puede dejar una receta apuntando a un
        # insumo inexistente, así que se bloquea el borrado.
        if self.recetas.has_for_insumo(insumo_id):
            raise ConflictError(
                "No se puede eliminar: el insumo está en la receta de un producto."
            )
        self.insumos.delete(insumo_id)
        self.session.commit()
