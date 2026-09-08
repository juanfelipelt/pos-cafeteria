import os
import secrets
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./pos-cafeteria.db")
    secret_key: str = ""
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )
    admin_email: str = os.getenv("ADMIN_EMAIL", "admin@cafeteriapos.com")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "admin123")
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")

    def __post_init__(self) -> None:
        env_secret = os.getenv("SECRET_KEY", "")
        if env_secret:
            self.secret_key = env_secret
        else:
            self.secret_key = secrets.token_hex(32)
            print(
                "AVISO: SECRET_KEY no está definida. Se generó una clave "
                "temporal; los tokens se invalidarán al reiniciar. Define "
                "SECRET_KEY en el entorno para producción."
            )

        if os.getenv("ADMIN_PASSWORD") is None:
            print(
                "AVISO: se usa la contraseña de admin por defecto (admin123). "
                "Define ADMIN_PASSWORD antes de desplegar."
            )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
