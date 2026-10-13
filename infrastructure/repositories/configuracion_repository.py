"""Repositorio SQLAlchemy para la configuración (clave-valor).

Implementa `ConfiguracionRepository` del dominio sobre la tabla
`configuraciones`. Permite leer, crear o actualizar ajustes del sistema.
"""

from __future__ import annotations
from sqlalchemy.orm import Session

from domain.entities.configuracion import Configuracion
from domain.repositories.configuracion_repository import ConfiguracionRepository
from infrastructure.models.configuracion import ConfiguracionModel


class SQLAlchemyConfiguracionRepository(ConfiguracionRepository):
    """Implementación concreta de `ConfiguracionRepository` con SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, clave: str) -> Configuracion | None:
        """Obtiene el valor de una configuración por su clave."""
        m = self.session.get(ConfiguracionModel, clave)
        # Si existe el modelo lo convertimos a entidad; si no, devolvemos None.
        return Configuracion(clave=m.clave, valor=m.valor) if m else None

    def set(self, clave: str, valor: str) -> Configuracion:
        """Crea o actualiza una configuración (upsert)."""
        m = self.session.get(ConfiguracionModel, clave)
        if m is None:
            # No existe: creamos una fila nueva.
            m = ConfiguracionModel(clave=clave, valor=valor)
            self.session.add(m)
        else:
            # Ya existe: solo actualizamos el valor.
            m.valor = valor
        self.session.flush()
        return Configuracion(clave=m.clave, valor=m.valor)

    def list(self) -> list[Configuracion]:
        """Devuelve todas las configuraciones registradas."""
        return [
            Configuracion(clave=m.clave, valor=m.valor)
            for m in self.session.query(ConfiguracionModel).all()
        ]
