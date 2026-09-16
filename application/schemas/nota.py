from pydantic import BaseModel


class NotaCreate(BaseModel):
    texto: str
    tipo: str = "nota"
    destinatario: str = "todos"
    prioridad: str = "normal"


class NotaUpdate(BaseModel):
    texto: str | None = None
    tipo: str | None = None
    destinatario: str | None = None
    prioridad: str | None = None
    hecho: bool | None = None
    archivada: bool | None = None
