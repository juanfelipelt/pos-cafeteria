from pydantic import BaseModel

from domain.entities.enums import MetodoPago


class ItemVenta(BaseModel):
    producto_id: str
    cantidad: int


class PagoInput(BaseModel):
    monto: float
    metodo: MetodoPago
    referencia: str | None = None


class VentaCreate(BaseModel):
    items: list[ItemVenta]
    pagos: list[PagoInput] = []


class PagoCreate(BaseModel):
    monto: float
    metodo: MetodoPago
    referencia: str | None = None
