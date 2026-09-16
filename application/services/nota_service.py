from sqlalchemy.orm import Session

from application.events import event_bus
from application.utils import new_id
from domain.entities.nota import Nota
from domain.entities.usuario import Usuario
from domain.exceptions import ForbiddenError, NotFoundError
from domain.repositories.nota_repository import NotaRepository


class NotaService:
    def __init__(self, notas: NotaRepository, session: Session) -> None:
        self.notas = notas
        self.session = session

    def _puede_editar(self, nota: Nota, usuario: Usuario) -> bool:
        return usuario.id == nota.autor_id or usuario.es_admin

    def crear(
        self,
        texto: str,
        tipo: str,
        destinatario: str,
        prioridad: str,
        autor: Usuario,
    ) -> Nota:
        nota = Nota(
            id=new_id(),
            texto=texto,
            tipo=tipo,
            destinatario=destinatario,
            prioridad=prioridad,
            autor_id=autor.id,
            autor_nombre=autor.nombre,
        )
        self.notas.add(nota)
        self.session.commit()
        event_bus.publish("nota_creada", nota.to_dict())
        return nota

    def listar(
        self,
        destinatario: str | None = None,
        tipo: str | None = None,
        incluir_archivadas: bool = False,
    ) -> list[Nota]:
        return self.notas.list(destinatario, tipo, incluir_archivadas)

    def obtener(self, nota_id: str) -> Nota:
        nota = self.notas.get(nota_id)
        if nota is None:
            raise NotFoundError("Nota no encontrada.")
        return nota

    def resumen(self) -> dict:
        activas = self.notas.list(incluir_archivadas=False)
        tareas = [n for n in activas if n.es_tarea]
        return {
            "tareas_pendientes": sum(1 for t in tareas if not t.hecho),
            "tareas_total": len(tareas),
            "notas": sum(1 for n in activas if not n.es_tarea),
            "pendientes": sum(1 for n in activas if n.pendiente),
        }

    def marcar_hecho(self, nota_id: str, hecho: bool) -> Nota:
        nota = self.obtener(nota_id)
        nota.marcar_hecho(hecho)
        self.notas.update(nota)
        self.session.commit()
        event_bus.publish("nota_actualizada", nota.to_dict())
        return nota

    def actualizar(
        self,
        nota_id: str,
        usuario: Usuario,
        texto: str | None = None,
        tipo: str | None = None,
        destinatario: str | None = None,
        prioridad: str | None = None,
        hecho: bool | None = None,
        archivada: bool | None = None,
    ) -> Nota:
        nota = self.obtener(nota_id)

        campos = {
            "texto": texto,
            "tipo": tipo,
            "destinatario": destinatario,
            "prioridad": prioridad,
            "archivada": archivada,
        }
        solo_estado = hecho is not None and all(v is None for v in campos.values())

        if not solo_estado and not self._puede_editar(nota, usuario):
            raise ForbiddenError("Solo el autor o un administrador pueden editarla.")

        if texto is not None:
            nota.cambiar_texto(texto)
        if tipo is not None:
            nota.cambiar_tipo(tipo)
        if destinatario is not None:
            nota.cambiar_destinatario(destinatario)
        if prioridad is not None:
            nota.cambiar_prioridad(prioridad)
        if hecho is not None:
            nota.marcar_hecho(hecho)
        if archivada is not None:
            if archivada:
                nota.archivar()
            else:
                nota.desarchivar()

        self.notas.update(nota)
        self.session.commit()
        event_bus.publish("nota_actualizada", nota.to_dict())
        return nota

    def eliminar(self, nota_id: str, usuario: Usuario) -> None:
        nota = self.obtener(nota_id)
        if not self._puede_editar(nota, usuario):
            raise ForbiddenError("Solo el autor o un administrador pueden eliminarla.")
        self.notas.delete(nota_id)
        self.session.commit()
        event_bus.publish("nota_eliminada", {"id": nota_id})
