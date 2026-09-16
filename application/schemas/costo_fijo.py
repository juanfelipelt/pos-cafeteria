from pydantic import BaseModel


class CostoFijoCreate(BaseModel):
    nombre: str
    monto: float = 0.0


class CostoFijoUpdate(BaseModel):
    nombre: str | None = None
    monto: float | None = None
    activo: bool | None = None
