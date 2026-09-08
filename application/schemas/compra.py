from pydantic import BaseModel


class ItemCompra(BaseModel):
    producto_id: str
    cantidad: int
    precio_unitario: float


class CompraCreate(BaseModel):
    proveedor_id: str
    items: list[ItemCompra]
