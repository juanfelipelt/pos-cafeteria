from dataclasses import dataclass, field
from datetime import datetime

from .enums import DestinatarioNota, PrioridadNota, TipoNota

_TIPOS = (TipoNota.TAREA.value, TipoNota.NOTA.value)
_DESTINATARIOS = (
    DestinatarioNota.TODOS.value,
    DestinatarioNota.ADMIN.value,
    DestinatarioNota.CAJERO.value,
)
_PRIORIDADES = (PrioridadNota.NORMAL.value, PrioridadNota.ALTA.value)


@dataclass
class Nota:
    """Entidad de dominio para una nota o tarea de la pizarra."""

    texto: str
    id: str | None = None
    tipo: str = TipoNota.NOTA.value
    destinatario: str = DestinatarioNota.TODOS.value
    prioridad: str = PrioridadNota.NORMAL.value
    autor_id: str | None = None
    autor_nombre: str = ""
    fecha_creacion: datetime = field(default_factory=datetime.now)
    hecho: bool = False
    archivada: bool = False

    def __post_init__(self) -> None:
        self.texto = self.texto.strip() if self.texto else ""
        if not self.texto:
            raise ValueError("El texto no puede estar vacío.")
        if self.tipo not in _TIPOS:
            raise ValueError("El tipo de nota no es válido.")
        if self.destinatario not in _DESTINATARIOS:
            raise ValueError("El destinatario no es válido.")
        if self.prioridad not in _PRIORIDADES:
            raise ValueError("La prioridad no es válida.")

    @property
    def es_tarea(self) -> bool:
        return self.tipo == TipoNota.TAREA.value

    @property
    def pendiente(self) -> bool:
        if self.archivada:
            return False
        if self.es_tarea:
            return not self.hecho
        return True

    def cambiar_texto(self, nuevo_texto: str) -> None:
        if not nuevo_texto or not nuevo_texto.strip():
            raise ValueError("El texto no puede estar vacío.")
        self.texto = nuevo_texto.strip()

    def cambiar_tipo(self, nuevo_tipo: str) -> None:
        if nuevo_tipo not in _TIPOS:
            raise ValueError("El tipo de nota no es válido.")
        self.tipo = nuevo_tipo

    def cambiar_destinatario(self, nuevo: str) -> None:
        if nuevo not in _DESTINATARIOS:
            raise ValueError("El destinatario no es válido.")
        self.destinatario = nuevo

    def cambiar_prioridad(self, nueva: str) -> None:
        if nueva not in _PRIORIDADES:
            raise ValueError("La prioridad no es válida.")
        self.prioridad = nueva

    def marcar_hecho(self, hecho: bool) -> None:
        self.hecho = hecho

    def archivar(self) -> None:
        self.archivada = True

    def desarchivar(self) -> None:
        self.archivada = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "texto": self.texto,
            "tipo": self.tipo,
            "destinatario": self.destinatario,
            "prioridad": self.prioridad,
            "autor_id": self.autor_id,
            "autor_nombre": self.autor_nombre,
            "fecha_creacion": self.fecha_creacion.isoformat(),
            "hecho": self.hecho,
            "archivada": self.archivada,
        }
