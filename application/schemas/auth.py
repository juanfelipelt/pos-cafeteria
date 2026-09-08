from pydantic import BaseModel

from domain.entities.enums import Rol


class LoginRequest(BaseModel):
    email: str
    password: str


class RegistrarRequest(BaseModel):
    nombre: str
    email: str
    password: str
    rol: Rol = Rol.CAJERO
