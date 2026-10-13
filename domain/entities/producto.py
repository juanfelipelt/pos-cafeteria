"""Entidad de dominio ``Producto``.

Un producto es lo que finalmente se vende al cliente. Puede obtenerse de tres
formas distintas (ver ``TipoProducto``): comprado ya terminado, preparado con
una receta de insumos, o compuesto como combo de otros productos/insumos.

Invariantes del negocio:
- El nombre es obligatorio.
- El precio, el stock y el costo nunca pueden ser negativos.
- El tipo debe ser "comprado", "preparado" o "compuesto".
"""

from dataclasses import dataclass

from .enums import TipoProducto


@dataclass
class Producto:
    """Entidad de dominio para un producto."""

    # Identificador único; None mientras no se haya guardado.
    id: str | None = None
    # Nombre comercial del producto (obligatorio).
    nombre: str = ""
    # Descripción libre para el menú.
    descripcion: str = ""
    # Categoría a la que pertenece (opcional).
    categoria_id: str | None = None
    # Ruta o URL de la imagen del producto.
    imagen: str = ""
    # Precio de venta al público.
    precio: float = 0.0
    # Unidades disponibles en inventario (entero).
    stock: int = 0
    # Borrado lógico: True = activo, False = desactivado.
    estado: bool = True
    # Forma de costeo del producto (comprado/preparado/compuesto).
    tipo: str = TipoProducto.COMPRADO.value
    # Costo de producción o de compra por unidad.
    costo: float = 0.0

    def __post_init__(self) -> None:
        """Valida todas las invariantes al crear el producto."""
        # El nombre no puede faltar ni ser solo espacios.
        if self.nombre is None or not self.nombre.strip():
            raise ValueError("El nombre del producto es obligatorio.")

        # Valores monetarios y de inventario no negativos.
        if self.precio < 0:
            raise ValueError("El precio del producto no puede ser negativo.")

        if self.stock < 0:
            raise ValueError("El stock del producto no puede ser negativo.")

        # El tipo debe estar dentro de los valores permitidos.
        if self.tipo not in (
            TipoProducto.COMPRADO.value,
            TipoProducto.PREPARADO.value,
            TipoProducto.COMPUESTO.value,
        ):
            raise ValueError("El tipo de producto no es válido.")

        if self.costo < 0:
            raise ValueError("El costo del producto no puede ser negativo.")

    @property
    def esta_disponible(self) -> bool:
        """El producto se puede vender solo si está activo y tiene existencias."""
        return self.estado and self.stock > 0

    def cambiar_nombre(self, nuevo_nombre: str) -> None:
        """Cambia el nombre validando que no quede vacío."""
        if not nuevo_nombre or not nuevo_nombre.strip():
            raise ValueError("El nuevo nombre no puede estar vacío.")
        self.nombre = nuevo_nombre.strip()

    def cambiar_descripcion(self, nueva_descripcion: str) -> None:
        """Actualiza la descripción. Si viene vacía, se deja en blanco."""
        self.descripcion = nueva_descripcion.strip() if nueva_descripcion else ""

    def cambiar_categoria_id(self, nueva_categoria_id: str | None) -> None:
        """Asigna o quita la categoría (acepta None para dejarlo sin categoría)."""
        self.categoria_id = (
            nueva_categoria_id.strip() if nueva_categoria_id else None
        )

    def cambiar_precio(self, nuevo_precio: float) -> None:
        """Actualiza el precio impidiendo valores negativos."""
        if nuevo_precio < 0:
            raise ValueError("El nuevo precio no puede ser negativo.")
        self.precio = nuevo_precio

    def cambiar_stock(self, nuevo_stock: int) -> None:
        """Actualiza el stock impidiendo valores negativos."""
        if nuevo_stock < 0:
            raise ValueError("El nuevo stock no puede ser negativo.")
        self.stock = nuevo_stock

    def cambiar_tipo(self, nuevo_tipo: str) -> None:
        """Cambia la forma de costeo validando el nuevo tipo."""
        if nuevo_tipo not in (
            TipoProducto.COMPRADO.value,
            TipoProducto.PREPARADO.value,
            TipoProducto.COMPUESTO.value,
        ):
            raise ValueError("El tipo de producto no es válido.")
        self.tipo = nuevo_tipo

    def cambiar_costo(self, nuevo_costo: float) -> None:
        """Actualiza el costo impidiendo valores negativos."""
        if nuevo_costo < 0:
            raise ValueError("El costo no puede ser negativo.")
        self.costo = nuevo_costo

    def desactivar(self) -> None:
        """Deshabilita el producto sin borrarlo (borrado lógico)."""
        self.estado = False

    def activar(self) -> None:
        """Vuelve a habilitar el producto."""
        self.estado = True

    def to_dict(self) -> dict:
        """Serializa el producto a un diccionario."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "categoria_id": self.categoria_id,
            "imagen": self.imagen,
            "precio": self.precio,
            "stock": self.stock,
            "estado": self.estado,
            "tipo": self.tipo,
            "costo": self.costo,
        }