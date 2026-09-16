from sqlalchemy import or_
from sqlalchemy.orm import Session

from domain.entities.nota import Nota
from domain.repositories.nota_repository import NotaRepository
from infrastructure.models.nota import NotaModel
from infrastructure.models.usuario import UsuarioModel


def _to_entity(m: NotaModel, autor_nombre: str | None = None) -> Nota:
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
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id: str) -> Nota | None:
        row = (
            self.session.query(NotaModel, UsuarioModel.nombre)
            .outerjoin(UsuarioModel, NotaModel.autor_id == UsuarioModel.id)
            .filter(NotaModel.id == id)
            .first()
        )
        if row is None:
            return None
        m, nombre = row
        return _to_entity(m, nombre)

    def list(
        self,
        destinatario: str | None = None,
        tipo: str | None = None,
        incluir_archivadas: bool = False,
    ) -> list[Nota]:
        q = self.session.query(NotaModel, UsuarioModel.nombre).outerjoin(
            UsuarioModel, NotaModel.autor_id == UsuarioModel.id
        )
        if not incluir_archivadas:
            q = q.filter(NotaModel.archivada.is_(False))
        if destinatario:
            q = q.filter(
                or_(
                    NotaModel.destinatario == destinatario,
                    NotaModel.destinatario == "todos",
                )
            )
        if tipo:
            q = q.filter(NotaModel.tipo == tipo)
        notas = [_to_entity(m, nombre) for m, nombre in q.all()]
        notas.sort(
            key=lambda n: (
                n.archivada,
                n.prioridad != "alta",
                -(n.fecha_creacion.timestamp() if n.fecha_creacion else 0),
            )
        )
        return notas

    def add(self, nota: Nota) -> Nota:
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
        m = self.session.get(NotaModel, id)
        if m is not None:
            self.session.delete(m)
            self.session.flush()
