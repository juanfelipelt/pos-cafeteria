from pydantic import BaseModel


class ItemReceta(BaseModel):
    tipo: str = "insumo"
    insumo_id: str | None = None
    componente_producto_id: str | None = None
    cantidad: float


class RecetaUpdate(BaseModel):
    items: list[ItemReceta]
