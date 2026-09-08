from pydantic import BaseModel, Field

from domain.entities.enums import Rol


class LoginRequest(BaseModel):
    email: str
    password: str


class RegistrarRequest(BaseModel):
    nombre: str
    email: str
    password: str = Field(min_length=8)
    rol: Rol = Rol.CAJERO
