import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./pos-cafeteria.db")
    secret_key: str = os.getenv("SECRET_KEY", "cambia-esta-clave-en-produccion")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )
    admin_email: str = os.getenv("ADMIN_EMAIL", "admin@cafeteriapos.com")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "admin123")


settings = Settings()
