from pydantic import BaseModel


class ProveedorCreate(BaseModel):
    nombre: str
    contacto: str
    telefono: str
    email: str = ""
    direccion: str = ""


class ProveedorUpdate(BaseModel):
    nombre: str | None = None
    contacto: str | None = None
    telefono: str | None = None
    email: str | None = None
    direccion: str | None = None
