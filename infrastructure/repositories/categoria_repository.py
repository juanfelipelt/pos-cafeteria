"""Repositorio SQLAlchemy para las categorías.

Implementa el puerto `CategoriaRepository` del dominio usando la tabla
`categorias` (modelo `CategoriaModel`). Traduce entre el modelo ORM y la
entidad de dominio `Categoria`.
"""

# `from __future__ import annotations` permite usar anotaciones de tipo modernas
# (como `str | None`) sin problemas en versiones antiguas de Python.
from __future__ import annotations
from sqlalchemy.orm import Session

# Entidad del dominio (lo que entiende la lógica de negocio).
from domain.entities.categoria import Categoria
# Puerto / interfaz que este repositorio implementa.
from domain.repositories.categoria_repository import CategoriaRepository
# Modelo ORM (tabla) que se usa para guardar en la base de datos.
from infrastructure.models.categoria import CategoriaModel


def _to_entity(m: CategoriaModel) -> Categoria:
    """Convierte un modelo ORM `CategoriaModel` en la entidad `Categoria`.

    Se usa para "sacar" los datos de la BD y entregarlos al dominio sin
    exponer detalles de SQLAlchemy.
    """
    return Categoria(
        id=m.id,
        nombre=m.nombre,
        descripcion=m.descripcion,
        estado=m.estado,
    )


class SQLAlchemyCategoriaRepository(CategoriaRepository):
    """Implementación concreta de `CategoriaRepository` con SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        # Guardamos la sesión de base de datos para usarla en cada método.
        self.session = session

    def get(self, id: str) -> Categoria | None:
        """Busca una categoría por su id. Devuelve None si no existe."""
        m = self.session.get(CategoriaModel, id)
        return _to_entity(m) if m else None

    def list(self) -> list[Categoria]:
        """Devuelve todas las categorías de la base de datos."""
        return [_to_entity(m) for m in self.session.query(CategoriaModel).all()]

    def add(self, categoria: Categoria) -> Categoria:
        """Crea una nueva categoría a partir de la entidad recibida."""
        # Creamos el modelo ORM copiando los campos de la entidad.
        m = CategoriaModel(
            id=categoria.id,
            nombre=categoria.nombre,
            descripcion=categoria.descripcion,
            estado=categoria.estado,
        )
        self.session.add(m)   # Marca el objeto para insertarlo.
        self.session.flush()  # Envía el INSERT a la BD dentro de la transacción.
        return categoria

    def update(self, categoria: Categoria) -> Categoria:
        """Actualiza una categoría existente con los datos de la entidad."""
        m = self.session.get(CategoriaModel, categoria.id)
        # Copiamos los campos editables al modelo ya cargado.
        m.nombre = categoria.nombre
        m.descripcion = categoria.descripcion
        m.estado = categoria.estado
        self.session.flush()  # Envía el UPDATE a la BD.
        return categoria
