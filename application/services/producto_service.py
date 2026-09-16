from sqlalchemy.orm import Session

from application.utils import new_id
from domain.entities.producto import Producto
from domain.exceptions import NotFoundError
from domain.repositories.producto_repository import ProductoRepository


class ProductoService:
    def __init__(self, productos: ProductoRepository, session: Session) -> None:
        self.productos = productos
        self.session = session

    def crear(
        self,
        nombre: str,
        descripcion: str = "",
        categoria_id: str | None = None,
        imagen: str = "",
        precio: float = 0.0,
        stock: int = 0,
        tipo: str = "comprado",
    ) -> Producto:
        producto = Producto(
            id=new_id(),
            nombre=nombre,
            descripcion=descripcion,
            categoria_id=categoria_id,
            imagen=imagen,
            precio=precio,
            stock=stock,
            tipo=tipo,
        )
        self.productos.add(producto)
        self.session.commit()
        return producto

    def listar(
        self,
        filtro: str | None = None,
        categoria_id: str | None = None,
        solo_activos: bool = False,
    ) -> list[Producto]:
        return self.productos.list(filtro, categoria_id, solo_activos)

    def obtener(self, producto_id: str) -> Producto:
        producto = self.productos.get(producto_id)
        if producto is None:
            raise NotFoundError("Producto no encontrado.")
        return producto

    def actualizar(
        self,
        producto_id: str,
        nombre: str | None = None,
        descripcion: str | None = None,
        categoria_id: str | None = None,
        imagen: str | None = None,
        precio: float | None = None,
        stock: int | None = None,
        tipo: str | None = None,
    ) -> Producto:
        producto = self.obtener(producto_id)
        if nombre is not None:
            producto.cambiar_nombre(nombre)
        if descripcion is not None:
            producto.cambiar_descripcion(descripcion)
        if categoria_id is not None:
            producto.cambiar_categoria_id(categoria_id)
        if imagen is not None:
            producto.imagen = imagen
        if precio is not None:
            producto.cambiar_precio(precio)
        if stock is not None:
            producto.cambiar_stock(stock)
        if tipo is not None:
            producto.cambiar_tipo(tipo)
        self.productos.update(producto)
        self.session.commit()
        return producto

    def cambiar_estado(self, producto_id: str, estado: bool) -> Producto:
        producto = self.obtener(producto_id)
        if estado:
            producto.activar()
        else:
            producto.desactivar()
        self.productos.update(producto)
        self.session.commit()
        return producto
