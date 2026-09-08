from pydantic import BaseModel


class LogoUpdate(BaseModel):
    logo: str
