from dataclasses import dataclass

@dataclass
class Producto:
    """Entidad de dominio para un producto."""

    id: str | None = None
    nombre: str = ""
    descripcion: str = ""
    categoria_id: str | None = None
    imagen: str = ""
    precio: float = 0.0
    stock: int = 0
    estado: bool = True

    def __post_init__(self) -> None:
        if self.nombre is None or not self.nombre.strip():
            raise ValueError("El nombre del producto es obligatorio.")

        if self.precio < 0:
            raise ValueError("El precio del producto no puede ser negativo.")

        if self.stock < 0:
            raise ValueError("El stock del producto no puede ser negativo.")

    @property
    def esta_disponible(self) -> bool:
        return self.estado and self.stock > 0

    def cambiar_nombre(self, nuevo_nombre: str) -> None:
        if not nuevo_nombre or not nuevo_nombre.strip():
            raise ValueError("El nuevo nombre no puede estar vacío.")
        self.nombre = nuevo_nombre.strip()

    def cambiar_descripcion(self, nueva_descripcion: str) -> None:
        self.descripcion = nueva_descripcion.strip() if nueva_descripcion else ""

    def cambiar_categoria_id(self, nueva_categoria_id: str | None) -> None:
        self.categoria_id = (
            nueva_categoria_id.strip() if nueva_categoria_id else None
        )

    def cambiar_precio(self, nuevo_precio: float) -> None:
        if nuevo_precio < 0:
            raise ValueError("El nuevo precio no puede ser negativo.")
        self.precio = nuevo_precio

    def cambiar_stock(self, nuevo_stock: int) -> None:
        if nuevo_stock < 0:
            raise ValueError("El nuevo stock no puede ser negativo.")
        self.stock = nuevo_stock

    def desactivar(self) -> None:
        self.estado = False

    def activar(self) -> None:
        self.estado = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "categoria_id": self.categoria_id,
            "imagen": self.imagen,
            "precio": self.precio,
            "stock": self.stock,
            "estado": self.estado,
        }