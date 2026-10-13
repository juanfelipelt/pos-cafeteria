"""Modelo ORM de la tabla `usuarios`.

Representa a las personas que usan el sistema (cajero, administrador, etc.).
Guarda sus datos de acceso; la contraseña NUNCA se guarda en texto plano,
solo su hash (resumen cifrado).
"""

# Boolean y String.
from sqlalchemy import Boolean, Column, String

from database import Base


class UsuarioModel(Base):
    """Tabla de usuarios del sistema."""

    __tablename__ = "usuarios"

    # Identificador único del usuario (clave primaria).
    id = Column(String, primary_key=True)
    # Nombre completo del usuario.
    nombre = Column(String, nullable=False)
    # Correo electrónico: debe ser único (unique=True) y se indexa (index=True)
    # porque se consulta con frecuencia al iniciar sesión.
    email = Column(String, nullable=False, unique=True, index=True)
    # Hash de la contraseña (no la contraseña en claro). Se escribe con "ñ"
    # respetando el nombre de la entidad del dominio.
    contraseña_hash = Column(String, nullable=False)
    # Rol del usuario (permisos). Por defecto "cajero".
    rol = Column(String, nullable=False, default="cajero")
    # Indica si el usuario está activo (True) o deshabilitado (False).
    estado = Column(Boolean, nullable=False, default=True)
