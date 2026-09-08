from sqlalchemy.orm import Session

from application.utils import new_id
from domain.entities.categoria import Categoria
from domain.exceptions import NotFoundError
from domain.repositories.categoria_repository import CategoriaRepository


class CategoriaService:
    def __init__(self, categorias: CategoriaRepository, session: Session) -> None:
        self.categorias = categorias
        self.session = session

    def crear(self, nombre: str, descripcion: str = "") -> Categoria:
        categoria = Categoria(id=new_id(), nombre=nombre, descripcion=descripcion)
        self.categorias.add(categoria)
        self.session.commit()
        return categoria

    def listar(self) -> list[Categoria]:
        return self.categorias.list()

    def obtener(self, categoria_id: str) -> Categoria:
        categoria = self.categorias.get(categoria_id)
        if categoria is None:
            raise NotFoundError("Categoría no encontrada.")
        return categoria

    def actualizar(
        self, categoria_id: str, nombre: str | None = None, descripcion: str | None = None
    ) -> Categoria:
        categoria = self.obtener(categoria_id)
        if nombre is not None:
            categoria.cambiar_nombre(nombre)
        if descripcion is not None:
            categoria.cambiar_descripcion(descripcion)
        self.categorias.update(categoria)
        self.session.commit()
        return categoria
