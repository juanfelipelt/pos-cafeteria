from pydantic import BaseModel


class ProductoCreate(BaseModel):
    nombre: str
    descripcion: str = ""
    categoria_id: str | None = None
    imagen: str = ""
    precio: float = 0.0
    stock: int = 0


class ProductoUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    categoria_id: str | None = None
    imagen: str | None = None
    precio: float | None = None
    stock: int | None = None


class EstadoRequest(BaseModel):
    estado: bool
