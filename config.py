"""Configuración central de la aplicación Cafetería POS.

Este archivo lee las variables de entorno (por ejemplo, la URL de la base de
datos, la clave secreta para firmar tokens JWT, credenciales del admin, etc.) y
las expone a través de un único objeto ``settings`` que el resto de la app importa.

Usa ``python-dotenv`` (``load_dotenv()``) para cargar un archivo ``.env`` si
existe, de modo que en desarrollo no haya que exportar variables manualmente.

Se relaciona con prácticamente todo el proyecto: ``database.py`` usa la URL de
conexión, los routers/seguridad usan la clave secreta y el tiempo de expiración
de tokens, y ``app.py`` usa el admin inicial y los orígenes CORS.
"""

import os
import secrets
from dataclasses import dataclass

from dotenv import load_dotenv

# Carga las variables definidas en el archivo .env (si existe) al entorno.
load_dotenv()


@dataclass
class Settings:
    """Contenedor tipado de toda la configuración de la aplicación.

    Cada atributo toma su valor de una variable de entorno o de un valor por
    defecto seguro (para desarrollo). Al instanciarla se valida/ajusta en
    ``__post_init__``.
    """

    # URL de conexión a la base de datos. Por defecto SQLite local.
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./pos-cafeteria.db")
    # Clave secreta para firmar tokens JWT. Se asigna en __post_init__.
    secret_key: str = ""
    # Algoritmo de firma de los tokens JWT.
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    # Minutos de vigencia de un token de acceso (se convierte a entero).
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )
    # Email del administrador que se crea por defecto al arrancar.
    admin_email: str = os.getenv("ADMIN_EMAIL", "admin@cafeteriapos.com")
    # Contraseña del administrador por defecto (cambiar en producción).
    admin_password: str = os.getenv("ADMIN_PASSWORD", "admin123")
    # Orígenes permitidos para CORS, separados por comas ("*" = todos).
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")

    def __post_init__(self) -> None:
        """Ajusta la configuración después de crear el objeto.

        - Asigna la ``secret_key``: usa ``SECRET_KEY`` del entorno o, si no
          existe, genera una aleatoria temporal (advirtiendo por consola).
        - Avisa si se está usando la contraseña de admin por defecto.

        Retorno:
            None
        """
        env_secret = os.getenv("SECRET_KEY", "")
        if env_secret:
            # Hay clave en el entorno: se usa tal cual.
            self.secret_key = env_secret
        else:
            # No hay clave: se genera una temporal. OJO: al reiniciar cambia,
            # por lo que los tokens emitidos antes dejarán de ser válidos.
            self.secret_key = secrets.token_hex(32)
            print(
                "AVISO: SECRET_KEY no está definida. Se generó una clave "
                "temporal; los tokens se invalidarán al reiniciar. Define "
                "SECRET_KEY en el entorno para producción."
            )

        # Avisa si no se configuró una contraseña de admin propia.
        if os.getenv("ADMIN_PASSWORD") is None:
            print(
                "AVISO: se usa la contraseña de admin por defecto (admin123). "
                "Define ADMIN_PASSWORD antes de desplegar."
            )

    @property
    def cors_origins_list(self) -> list[str]:
        """Convierte la cadena de orígenes CORS en una lista limpia.

        Retorno:
            list[str]: orígenes sin espacios sobrantes y sin elementos vacíos.
        """
        # Separa por comas, recorta espacios y descarta cadenas vacías.
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


# Instancia única (singleton) de configuración que importa el resto de la app.
settings = Settings()
