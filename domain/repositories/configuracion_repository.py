from abc import ABC, abstractmethod

from domain.entities.configuracion import Configuracion


class ConfiguracionRepository(ABC):
    @abstractmethod
    def get(self, clave: str) -> Configuracion | None:
        ...

    @abstractmethod
    def set(self, clave: str, valor: str) -> Configuracion:
        ...

    @abstractmethod
    def list(self) -> list[Configuracion]:
        ...
