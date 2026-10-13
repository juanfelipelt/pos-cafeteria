"""Servicio de configuración (caso de uso: "Parámetros del negocio").

¿Qué resuelve?
- Guardar y leer pares clave/valor que parametrizan el sistema (por ejemplo,
  los días laborables usados en el costeo, o datos de la empresa).

¿Cómo usa los repositorios?
- Recibe un ``ConfiguracionRepository`` que implementa ``list``, ``get`` y
  ``set`` sobre la tabla de configuración.
- Recibe una ``Session`` para confirmar los cambios.

Es un servicio muy delgado: solo traduce el repositorio a un diccionario
cómodo para el resto de la aplicación.
"""

from sqlalchemy.orm import Session

from domain.entities.configuracion import Configuracion
from domain.repositories.configuracion_repository import ConfiguracionRepository


class ConfiguracionService:
    """Expone la configuración clave/valor del negocio."""

    def __init__(self, configuraciones: ConfiguracionRepository, session: Session) -> None:
        """Guarda las dependencias del servicio.

        Parámetros:
            configuraciones: repositorio de configuración.
            session: sesión de SQLAlchemy para confirmar cambios.
        """
        self.configuraciones = configuraciones
        self.session = session

    def obtener_todas(self) -> dict:
        """Devuelve toda la configuración como un diccionario clave -> valor.

        Retorna:
            Diccionario con todos los parámetros configurados.
        """
        # Se recorre la lista de entidades y se arma el mapa clave/valor.
        return {c.clave: c.valor for c in self.configuraciones.list()}

    def obtener(self, clave: str) -> str | None:
        """Lee el valor de una clave de configuración.

        Parámetros:
            clave: nombre del parámetro.

        Retorna:
            El valor de la clave, o ``None`` si no está configurada.
        """
        c = self.configuraciones.get(clave)
        return c.valor if c else None

    def establecer(self, clave: str, valor: str) -> Configuracion:
        """Crea o actualiza una clave de configuración.

        Parámetros:
            clave: nombre del parámetro.
            valor: valor a guardar.

        Retorna:
            La configuración guardada.
        """
        c = self.configuraciones.set(clave, valor)
        self.session.commit()
        return c
