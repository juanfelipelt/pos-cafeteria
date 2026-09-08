from pydantic import BaseModel


class CategoriaCreate(BaseModel):
    nombre: str
    descripcion: str = ""


class CategoriaUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
