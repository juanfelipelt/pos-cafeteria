from sqlalchemy.orm import Session

from domain.entities.configuracion import Configuracion
from domain.repositories.configuracion_repository import ConfiguracionRepository


class ConfiguracionService:
    def __init__(self, configuraciones: ConfiguracionRepository, session: Session) -> None:
        self.configuraciones = configuraciones
        self.session = session

    def obtener_todas(self) -> dict:
        return {c.clave: c.valor for c in self.configuraciones.list()}

    def obtener(self, clave: str) -> str | None:
        c = self.configuraciones.get(clave)
        return c.valor if c else None

    def establecer(self, clave: str, valor: str) -> Configuracion:
        c = self.configuraciones.set(clave, valor)
        self.session.commit()
        return c
