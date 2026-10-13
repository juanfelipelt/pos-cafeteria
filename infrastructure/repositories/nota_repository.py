"""Repositorio SQLAlchemy para las notas internas.

Implementa `NotaRepository` del dominio sobre la tabla `notas`. Además de las
operaciones básicas, une cada nota con el nombre de su autor (usuario) y aplica
un orden especial (pendientes y de alta prioridad primero).
"""

from __future__ import annotations
# `or_` permite combinar condiciones con OR dentro de un filter.
from sqlalchemy import or_
from sqlalchemy.orm import Session

from domain.entities.nota import Nota
from domain.repositories.nota_repository import NotaRepository
from infrastructure.models.nota import NotaModel
from infrastructure.models.usuario import UsuarioModel


def _to_entity(m: NotaModel, autor_nombre: str | None = None) -> Nota:
    """Convierte un modelo ORM `NotaModel` en la entidad `Nota`.

    `autor_nombre` viene de unir (join) con la tabla de usuarios; puede ser
    None si la nota no tiene autor o este no existe.
    """
    return Nota(
        id=m.id,
        texto=m.texto,
        tipo=m.tipo,
        destinatario=m.destinatario,
        prioridad=m.prioridad,
        autor_id=m.autor_id,
        autor_nombre=autor_nombre or "",
        fecha_creacion=m.fecha_creacion,
        hecho=m.hecho,
        archivada=m.archivada,
    )


class SQLAlchemyNotaRepository(NotaRepository):
    """Implementación concreta de `NotaRepository` con SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id: str) -> Nota | None:
        """Busca una nota por id, incluyendo el nombre de su autor."""
        # outerjoin: trae la nota aunque no tenga autor (o el autor no exista).
        row = (
            self.session.query(NotaModel, UsuarioModel.nombre)
            .outerjoin(UsuarioModel, NotaModel.autor_id == UsuarioModel.id)
            .filter(NotaModel.id == id)
            .first()
        )
        if row is None:
            return None
        m, nombre = row  # La consulta devuelve una tupla (nota, nombre_autor).
        return _to_entity(m, nombre)

    def list(
        self,
        destinatario: str | None = None,
        tipo: str | None = None,
        incluir_archivadas: bool = False,
    ) -> list[Nota]:
        """Lista notas con filtros y un orden pensado para la pizarra.

        - Solo trae notas dirigidas a `destinatario` o a "todos".
        - Por defecto oculta las archivadas (salvo `incluir_archivadas=True`).
        - Orden: primero no archivadas, luego prioridad alta, luego más recientes.
        """
        q = self.session.query(NotaModel, UsuarioModel.nombre).outerjoin(
            UsuarioModel, NotaModel.autor_id == UsuarioModel.id
        )
        if not incluir_archivadas:
            q = q.filter(NotaModel.archivada.is_(False))
        if destinatario:
            # Una nota se muestra si va dirigida a la persona o a "todos".
            q = q.filter(
                or_(
                    NotaModel.destinatario == destinatario,
                    NotaModel.destinatario == "todos",
                )
            )
        if tipo:
            q = q.filter(NotaModel.tipo == tipo)
        notas = [_to_entity(m, nombre) for m, nombre in q.all()]
        # Ordenamos en Python (no en SQL) por la clave compuesta:
        #   1) archivada: False (0) va antes que True (1).
        #   2) prioridad != "alta": False (0) va antes que True (1).
        #   3) fecha más reciente primero (negamos el timestamp).
        notas.sort(
            key=lambda n: (
                n.archivada,
                n.prioridad != "alta",
                -(n.fecha_creacion.timestamp() if n.fecha_creacion else 0),
            )
        )
        return notas

    def add(self, nota: Nota) -> Nota:
        """Registra una nueva nota."""
        m = NotaModel(
            id=nota.id,
            texto=nota.texto,
            tipo=nota.tipo,
            destinatario=nota.destinatario,
            prioridad=nota.prioridad,
            autor_id=nota.autor_id,
            fecha_creacion=nota.fecha_creacion,
            hecho=nota.hecho,
            archivada=nota.archivada,
        )
        self.session.add(m)
        self.session.flush()
        return nota

    def update(self, nota: Nota) -> Nota:
        """Actualiza una nota existente (texto, estado, prioridad, etc.)."""
        m = self.session.get(NotaModel, nota.id)
        m.texto = nota.texto
        m.tipo = nota.tipo
        m.destinatario = nota.destinatario
        m.prioridad = nota.prioridad
        m.hecho = nota.hecho
        m.archivada = nota.archivada
        self.session.flush()
        return nota

    def delete(self, id: str) -> None:
        """Elimina una nota si existe."""
        m = self.session.get(NotaModel, id)
        if m is not None:
            self.session.delete(m)
            self.session.flush()
