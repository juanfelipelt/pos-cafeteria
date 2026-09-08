from sqlalchemy.orm import Session

from domain.entities.configuracion import Configuracion
from domain.repositories.configuracion_repository import ConfiguracionRepository
from infrastructure.models.configuracion import ConfiguracionModel


class SQLAlchemyConfiguracionRepository(ConfiguracionRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, clave: str) -> Configuracion | None:
        m = self.session.get(ConfiguracionModel, clave)
        return Configuracion(clave=m.clave, valor=m.valor) if m else None

    def set(self, clave: str, valor: str) -> Configuracion:
        m = self.session.get(ConfiguracionModel, clave)
        if m is None:
            m = ConfiguracionModel(clave=clave, valor=valor)
            self.session.add(m)
        else:
            m.valor = valor
        self.session.flush()
        return Configuracion(clave=m.clave, valor=m.valor)

    def list(self) -> list[Configuracion]:
        return [
            Configuracion(clave=m.clave, valor=m.valor)
            for m in self.session.query(ConfiguracionModel).all()
        ]
