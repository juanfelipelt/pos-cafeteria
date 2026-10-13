"""Schemas (DTOs) de autenticación.

Este módulo define los modelos Pydantic que describen los datos que el cliente
(por ejemplo la app o el frontend) envía al backend cuando un usuario quiere
iniciar sesión o registrarse.

¿Qué es un schema?
------------------
En este proyecto los "schemas" son DTOs (Data Transfer Objects): objetos que
solo transportan y validan información entre las capas de la aplicación.
Sirven como contrato de entrada/salida de la API y NO contienen lógica de
negocio; esa lógica vive en los casos de uso y en las entidades del dominio.

Relación con el resto del proyecto:
- La capa de presentación (routers de FastAPI) recibe estos modelos como
  cuerpo de las peticiones HTTP.
- Tras validarse con Pydantic, los datos se entregan a los casos de uso,
  que sí contienen las reglas de negocio (incluida la verificación de la
  contraseña usando el módulo de security).
"""

from pydantic import BaseModel, Field

from domain.entities.enums import Rol


class LoginRequest(BaseModel):
    """Datos mínimos para iniciar sesión."""

    # Correo con el que se identifica el usuario.
    email: str
    # Contraseña en texto plano; se comparará contra el hash guardado.
    password: str


class RegistrarRequest(BaseModel):
    """Datos necesarios para crear/registrar un nuevo usuario."""

    # Nombre visible del usuario.
    nombre: str
    # Correo único que servirá como identificador de acceso.
    email: str
    # Contraseña: Pydantic exige al menos 8 caracteres antes de continuar.
    password: str = Field(min_length=8)
    # Rol (permiso) del usuario; si no se especifica se asume CAJERO.
    rol: Rol = Rol.CAJERO
