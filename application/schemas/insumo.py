from pydantic import BaseModel


class InsumoCreate(BaseModel):
    nombre: str
    unidad: str
    stock: float = 0.0
    costo_unitario: float = 0.0
    proveedor_id: str | None = None


class InsumoUpdate(BaseModel):
    nombre: str | None = None
    unidad: str | None = None
    stock: float | None = None
    costo_unitario: float | None = None
    proveedor_id: str | None = None


class InsumoEstadoRequest(BaseModel):
    estado: bool
