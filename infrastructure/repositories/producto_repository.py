from sqlalchemy import func
from sqlalchemy.orm import Session

from domain.entities.producto import Producto
from domain.repositories.producto_repository import ProductoRepository
from infrastructure.models.producto import ProductoModel


def _to_entity(m: ProductoModel) -> Producto:
    return Producto(
        id=m.id,
        nombre=m.nombre,
        descripcion=m.descripcion,
        categoria_id=m.categoria_id,
        imagen=m.imagen,
        precio=m.precio,
        stock=m.stock,
        estado=m.estado,
        tipo=m.tipo,
        costo=m.costo,
    )


class SQLAlchemyProductoRepository(ProductoRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id: str) -> Producto | None:
        m = self.session.get(ProductoModel, id)
        return _to_entity(m) if m else None

    def list(
        self,
        filtro: str | None = None,
        categoria_id: str | None = None,
        solo_activos: bool = False,
    ) -> list[Producto]:
        q = self.session.query(ProductoModel)
        if filtro:
            q = q.filter(ProductoModel.nombre.ilike(f"%{filtro}%"))
        if categoria_id:
            q = q.filter(ProductoModel.categoria_id == categoria_id)
        if solo_activos:
            q = q.filter(ProductoModel.estado.is_(True))
        q = q.order_by(func.lower(ProductoModel.nombre).asc(), ProductoModel.nombre.asc())
        return [_to_entity(m) for m in q.all()]

    def add(self, producto: Producto) -> Producto:
        m = ProductoModel(
            id=producto.id,
            nombre=producto.nombre,
            descripcion=producto.descripcion,
            categoria_id=producto.categoria_id,
            imagen=producto.imagen,
            precio=producto.precio,
            stock=producto.stock,
            estado=producto.estado,
            tipo=producto.tipo,
            costo=producto.costo,
        )
        self.session.add(m)
        self.session.flush()
        return producto

    def update(self, producto: Producto) -> Producto:
        m = self.session.get(ProductoModel, producto.id)
        m.nombre = producto.nombre
        m.descripcion = producto.descripcion
        m.categoria_id = producto.categoria_id
        m.imagen = producto.imagen
        m.precio = producto.precio
        m.stock = producto.stock
        m.estado = producto.estado
        m.tipo = producto.tipo
        m.costo = producto.costo
        self.session.flush()
        return producto
