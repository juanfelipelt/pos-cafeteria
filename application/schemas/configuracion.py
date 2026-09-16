from pydantic import BaseModel


class LogoUpdate(BaseModel):
    logo: str


class ConfiguracionUpdate(BaseModel):
    valor: str
