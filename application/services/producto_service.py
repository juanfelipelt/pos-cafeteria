"""Servicio de productos (caso de uso: "Catálogo de productos").

¿Qué resuelve?
- Administrar los productos que se venden: nombre, descripción, categoría,
  imagen, precio, stock y tipo (comprado, preparado o compuesto).

¿Cómo usa los repositorios?
- ``ProductoRepository``: CRUD y listados con filtros de productos.
- ``Session``: confirma los cambios.

El ``tipo`` de producto es importante para el costeo: "comprado" usa su costo
de compras, mientras que "preparado" y "compuesto" se costean por su receta.
"""

from sqlalchemy.orm import Session

from application.utils import new_id
from domain.entities.producto import Producto
from domain.exceptions import NotFoundError
from domain.repositories.producto_repository import ProductoRepository


class ProductoService:
    """Gestiona el catálogo de productos."""

    def __init__(self, productos: ProductoRepository, session: Session) -> None:
        """Guarda las dependencias del servicio.

        Parámetros:
            productos: repositorio de productos.
            session: sesión de SQLAlchemy para confirmar cambios.
        """
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
        """Crea un producto nuevo.

        Parámetros:
            nombre: nombre del producto.
            descripcion: descripción corta (opcional).
            categoria_id: categoría a la que pertenece (opcional).
            imagen: ruta o URL de la imagen (opcional).
            precio: precio de venta; por defecto 0.
            stock: existencias iniciales; por defecto 0.
            tipo: "comprado", "preparado" o "compuesto".

        Retorna:
            El producto creado y confirmado.
        """
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
        """Lista productos con filtros opcionales.

        Parámetros:
            filtro: texto a buscar en el nombre (opcional).
            categoria_id: filtrar por categoría (opcional).
            solo_activos: si es ``True``, excluye los inactivos.

        Retorna:
            Lista de productos que cumplen los criterios.
        """
        return self.productos.list(filtro, categoria_id, solo_activos)

    def obtener(self, producto_id: str) -> Producto:
        """Busca un producto por id.

        Parámetros:
            producto_id: identificador del producto.

        Retorna:
            El producto encontrado.

        Lanza:
            NotFoundError: si no existe.
        """
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
        """Actualiza los campos enviados de un producto.

        Solo se modifican los valores distintos de ``None``.

        Parámetros:
            producto_id: id del producto a modificar.
            nombre, descripcion, categoria_id, imagen, precio, stock, tipo:
                nuevos valores (opcionales).

        Retorna:
            El producto actualizado.

        Lanza:
            NotFoundError: si no existe.
        """
        producto = self.obtener(producto_id)
        # Cada campo se cambia solo si fue enviado (no es None).
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
        """Activa o desactiva un producto (disponibilidad para la venta).

        Parámetros:
            producto_id: id del producto.
            estado: ``True`` para activar, ``False`` para desactivar.

        Retorna:
            El producto con su nuevo estado.

        Lanza:
            NotFoundError: si no existe.
        """
        producto = self.obtener(producto_id)
        if estado:
            producto.activar()
        else:
            producto.desactivar()
        self.productos.update(producto)
        self.session.commit()
        return producto
