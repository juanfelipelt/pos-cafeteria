from pydantic import BaseModel


class ItemCompra(BaseModel):
    tipo: str = "producto"
    producto_id: str | None = None
    insumo_id: str | None = None
    cantidad: float
    precio_unitario: float


class CompraCreate(BaseModel):
    proveedor_id: str
    items: list[ItemCompra]
