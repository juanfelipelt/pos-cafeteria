"""Entidad de dominio ``Nota``.

Representa un mensaje de la **pizarra** del equipo. Puede ser una simple nota
informativa o una tarea que debe completarse. Las notas se pueden dirigir a
todos, a los administradores o a los cajeros, y tienen una prioridad.

Invariantes del negocio:
- El texto no puede estar vacío.
- ``tipo``, ``destinatario`` y ``prioridad`` deben ser valores permitidos.
"""

from dataclasses import dataclass, field
from datetime import datetime

from .enums import DestinatarioNota, PrioridadNota, TipoNota

# Tuplas con los valores válidos. Se definen una sola vez para reutilizarlos
# en las validaciones (así agregar una opción nueva se hace en un solo lugar).
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

    # Contenido del mensaje (obligatorio).
    texto: str
    # Identificador único; None mientras no se haya guardado.
    id: str | None = None
    # "nota" (informativa) o "tarea" (pendiente de completar).
    tipo: str = TipoNota.NOTA.value
    # A quién va dirigida (todos/admin/cajero).
    destinatario: str = DestinatarioNota.TODOS.value
    # Urgencia: "normal" o "alta".
    prioridad: str = PrioridadNota.NORMAL.value
    # Quién creó la nota (id y nombre para mostrarlo sin consultas extra).
    autor_id: str | None = None
    autor_nombre: str = ""
    # Momento en que se creó la nota.
    fecha_creacion: datetime = field(default_factory=datetime.now)
    # Solo aplica a tareas: True cuando ya se completó.
    hecho: bool = False
    # True cuando la nota se archivó (se oculta de la pizarra activa).
    archivada: bool = False

    def __post_init__(self) -> None:
        """Normaliza el texto y valida los campos enumerados."""
        # Se limpia el texto; si queda vacío, es un error.
        self.texto = self.texto.strip() if self.texto else ""
        if not self.texto:
            raise ValueError("El texto no puede estar vacío.")
        # Cada campo debe pertenecer a su lista de valores permitidos.
        if self.tipo not in _TIPOS:
            raise ValueError("El tipo de nota no es válido.")
        if self.destinatario not in _DESTINATARIOS:
            raise ValueError("El destinatario no es válido.")
        if self.prioridad not in _PRIORIDADES:
            raise ValueError("La prioridad no es válida.")

    @property
    def es_tarea(self) -> bool:
        """Indica si la nota es realmente una tarea."""
        return self.tipo == TipoNota.TAREA.value

    @property
    def pendiente(self) -> bool:
        """Indica si la nota sigue pendiente de atención.

        Reglas:
        - Una nota archivada nunca está pendiente.
        - Una tarea está pendiente mientras no se marque como hecha.
        - Una nota simple siempre está pendiente (mientras no se archive).
        """
        if self.archivada:
            return False
        if self.es_tarea:
            return not self.hecho
        return True

    def cambiar_texto(self, nuevo_texto: str) -> None:
        """Actualiza el texto validando que no quede vacío."""
        if not nuevo_texto or not nuevo_texto.strip():
            raise ValueError("El texto no puede estar vacío.")
        self.texto = nuevo_texto.strip()

    def cambiar_tipo(self, nuevo_tipo: str) -> None:
        """Cambia el tipo (nota/tarea) validando que sea válido."""
        if nuevo_tipo not in _TIPOS:
            raise ValueError("El tipo de nota no es válido.")
        self.tipo = nuevo_tipo

    def cambiar_destinatario(self, nuevo: str) -> None:
        """Cambia el destinatario validando que sea válido."""
        if nuevo not in _DESTINATARIOS:
            raise ValueError("El destinatario no es válido.")
        self.destinatario = nuevo

    def cambiar_prioridad(self, nueva: str) -> None:
        """Cambia la prioridad validando que sea válida."""
        if nueva not in _PRIORIDADES:
            raise ValueError("La prioridad no es válida.")
        self.prioridad = nueva

    def marcar_hecho(self, hecho: bool) -> None:
        """Marca o desmarca una tarea como completada."""
        self.hecho = hecho

    def archivar(self) -> None:
        """Archiva la nota (deja de mostrarse en la pizarra activa)."""
        self.archivada = True

    def desarchivar(self) -> None:
        """Devuelve la nota a la pizarra activa."""
        self.archivada = False

    def to_dict(self) -> dict:
        """Serializa la nota a un diccionario."""
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
