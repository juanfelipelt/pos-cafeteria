from sqlalchemy.orm import Session

from domain.entities.categoria import Categoria
from domain.repositories.categoria_repository import CategoriaRepository
from infrastructure.models.categoria import CategoriaModel


def _to_entity(m: CategoriaModel) -> Categoria:
    return Categoria(
        id=m.id,
        nombre=m.nombre,
        descripcion=m.descripcion,
        estado=m.estado,
    )


class SQLAlchemyCategoriaRepository(CategoriaRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id: str) -> Categoria | None:
        m = self.session.get(CategoriaModel, id)
        return _to_entity(m) if m else None

    def list(self) -> list[Categoria]:
        return [_to_entity(m) for m in self.session.query(CategoriaModel).all()]

    def add(self, categoria: Categoria) -> Categoria:
        m = CategoriaModel(
            id=categoria.id,
            nombre=categoria.nombre,
            descripcion=categoria.descripcion,
            estado=categoria.estado,
        )
        self.session.add(m)
        self.session.flush()
        return categoria

    def update(self, categoria: Categoria) -> Categoria:
        m = self.session.get(CategoriaModel, categoria.id)
        m.nombre = categoria.nombre
        m.descripcion = categoria.descripcion
        m.estado = categoria.estado
        self.session.flush()
        return categoria
