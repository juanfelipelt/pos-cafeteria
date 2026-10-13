"""Servicio de categorías (caso de uso: "Categorías de productos").

¿Qué resuelve?
- Agrupar los productos del negocio en categorías (por ejemplo: bebidas,
  comidas, postres) para poder filtrarlos y organizarlos.

¿Cómo usa los repositorios?
- Recibe un ``CategoriaRepository`` que encapsula el acceso a datos.
- Recibe una ``Session`` de SQLAlchemy para confirmar los cambios.

Es un CRUD sencillo de la capa de aplicación: valida la existencia y aplica
los cambios a través de la propia entidad de dominio.
"""

from sqlalchemy.orm import Session

from application.utils import new_id
from domain.entities.categoria import Categoria
from domain.exceptions import NotFoundError
from domain.repositories.categoria_repository import CategoriaRepository


class CategoriaService:
    """Gestiona el ciclo de vida de las categorías de productos."""

    def __init__(self, categorias: CategoriaRepository, session: Session) -> None:
        """Guarda las dependencias del servicio.

        Parámetros:
            categorias: repositorio de categorías.
            session: sesión de SQLAlchemy para confirmar cambios.
        """
        self.categorias = categorias
        self.session = session

    def crear(self, nombre: str, descripcion: str = "") -> Categoria:
        """Crea una nueva categoría.

        Parámetros:
            nombre: nombre de la categoría.
            descripcion: texto opcional que describe la categoría.

        Retorna:
            La categoría creada y confirmada.
        """
        # Se genera un id único y se construye la entidad de dominio.
        categoria = Categoria(id=new_id(), nombre=nombre, descripcion=descripcion)
        self.categorias.add(categoria)
        self.session.commit()
        return categoria

    def listar(self) -> list[Categoria]:
        """Devuelve todas las categorías.

        Retorna:
            Lista de categorías.
        """
        return self.categorias.list()

    def obtener(self, categoria_id: str) -> Categoria:
        """Busca una categoría por id.

        Parámetros:
            categoria_id: identificador de la categoría.

        Retorna:
            La categoría encontrada.

        Lanza:
            NotFoundError: si la categoría no existe.
        """
        categoria = self.categorias.get(categoria_id)
        # Si no existe, se avisa al llamador con un error de dominio.
        if categoria is None:
            raise NotFoundError("Categoría no encontrada.")
        return categoria

    def actualizar(
        self, categoria_id: str, nombre: str | None = None, descripcion: str | None = None
    ) -> Categoria:
        """Actualiza el nombre y/o la descripción de una categoría.

        Solo se aplican los campos enviados (los que no vienen en ``None``).

        Parámetros:
            categoria_id: identificador de la categoría a modificar.
            nombre: nuevo nombre (opcional).
            descripcion: nueva descripción (opcional).

        Retorna:
            La categoría actualizada.

        Lanza:
            NotFoundError: si la categoría no existe.
        """
        # obtener() valida que la categoría exista o lanza NotFoundError.
        categoria = self.obtener(categoria_id)
        # Se cambia solo lo que el llamador envió (None = no tocar).
        if nombre is not None:
            categoria.cambiar_nombre(nombre)
        if descripcion is not None:
            categoria.cambiar_descripcion(descripcion)
        self.categorias.update(categoria)
        self.session.commit()
        return categoria
