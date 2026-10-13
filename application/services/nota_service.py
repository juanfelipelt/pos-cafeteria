"""Servicio de notas/tareas (caso de uso: "Pizarra de notas y tareas").

¿Qué resuelve?
- Administrar la pizarra colaborativa del negocio: notas y tareas dirigidas
  a un destinatario (todos, admin, cajero) con prioridad y estado.
- Aplicar reglas de permisos: solo el autor o un administrador pueden editar
  o eliminar una nota.
- Publicar eventos en el bus para que la interfaz se actualice en tiempo real.

¿Cómo usa los repositorios?
- ``NotaRepository``: CRUD de notas.
- ``Session``: confirma los cambios.
- ``event_bus``: publica eventos (nota_creada, nota_actualizada,
  nota_eliminada) que se emiten a los clientes conectados por SSE.
"""

from sqlalchemy.orm import Session

from application.events import event_bus
from application.utils import new_id
from domain.entities.nota import Nota
from domain.entities.usuario import Usuario
from domain.exceptions import ForbiddenError, NotFoundError
from domain.repositories.nota_repository import NotaRepository


class NotaService:
    """Gestiona notas y tareas de la pizarra."""

    def __init__(self, notas: NotaRepository, session: Session) -> None:
        """Guarda las dependencias del servicio.

        Parámetros:
            notas: repositorio de notas.
            session: sesión de SQLAlchemy para confirmar cambios.
        """
        self.notas = notas
        self.session = session

    def _puede_editar(self, nota: Nota, usuario: Usuario) -> bool:
        """Indica si un usuario puede editar/eliminar una nota.

        Regla: puede el autor de la nota o cualquier administrador.

        Parámetros:
            nota: nota sobre la que se quiere operar.
            usuario: usuario que intenta la operación.

        Retorna:
            ``True`` si tiene permiso, ``False`` en caso contrario.
        """
        return usuario.id == nota.autor_id or usuario.es_admin

    def crear(
        self,
        texto: str,
        tipo: str,
        destinatario: str,
        prioridad: str,
        autor: Usuario,
    ) -> Nota:
        """Crea una nota o tarea nueva.

        Parámetros:
            texto: contenido de la nota.
            tipo: "nota" o "tarea".
            destinatario: a quién va dirigida (todos, admin, cajero).
            prioridad: prioridad de la nota (normal, alta).
            autor: usuario que la crea.

        Retorna:
            La nota creada y confirmada.
        """
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
        # Se avisa a los clientes en tiempo real que hay una nota nueva.
        event_bus.publish("nota_creada", nota.to_dict())
        return nota

    def listar(
        self,
        destinatario: str | None = None,
        tipo: str | None = None,
        incluir_archivadas: bool = False,
    ) -> list[Nota]:
        """Lista notas con filtros opcionales.

        Parámetros:
            destinatario: filtrar por destinatario (opcional).
            tipo: filtrar por tipo (opcional).
            incluir_archivadas: si es ``False`` (por defecto), oculta las
                notas archivadas.

        Retorna:
            Lista de notas que cumplen los filtros.
        """
        return self.notas.list(destinatario, tipo, incluir_archivadas)

    def obtener(self, nota_id: str) -> Nota:
        """Busca una nota por id.

        Parámetros:
            nota_id: identificador de la nota.

        Retorna:
            La nota encontrada.

        Lanza:
            NotFoundError: si no existe.
        """
        nota = self.notas.get(nota_id)
        if nota is None:
            raise NotFoundError("Nota no encontrada.")
        return nota

    def resumen(self) -> dict:
        """Resume el estado de la pizarra (solo notas activas).

        Retorna:
            Diccionario con tareas pendientes, total de tareas, cantidad de
            notas y notas pendientes.
        """
        activas = self.notas.list(incluir_archivadas=False)
        # Solo las tareas se cuentan como pendientes/hechas.
        tareas = [n for n in activas if n.es_tarea]
        return {
            "tareas_pendientes": sum(1 for t in tareas if not t.hecho),
            "tareas_total": len(tareas),
            "notas": sum(1 for n in activas if not n.es_tarea),
            "pendientes": sum(1 for n in activas if n.pendiente),
        }

    def marcar_hecho(self, nota_id: str, hecho: bool) -> Nota:
        """Marca una tarea como hecha o pendiente.

        Parámetros:
            nota_id: id de la nota/tarea.
            hecho: ``True`` para marcarla hecha, ``False`` para pendiente.

        Retorna:
            La nota actualizada.

        Lanza:
            NotFoundError: si no existe.
        """
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
        """Actualiza una nota aplicando permisos.

        Truco de permisos: si el único cambio es marcar ``hecho``, se permite
        a cualquiera (por ejemplo, el cajero destinatario) sin exigir ser el
        autor. Para cualquier otro cambio se aplica ``_puede_editar``.

        Parámetros:
            nota_id: id de la nota.
            usuario: usuario que solicita el cambio.
            texto, tipo, destinatario, prioridad, hecho, archivada: campos a
                modificar (los que lleguen en ``None`` no se tocan).

        Retorna:
            La nota actualizada.

        Lanza:
            NotFoundError: si no existe.
            ForbiddenError: si el usuario no tiene permiso.
        """
        nota = self.obtener(nota_id)

        # Mapa de los campos "de contenido" para detectar si solo se cambió
        # el estado de hecho.
        campos = {
            "texto": texto,
            "tipo": tipo,
            "destinatario": destinatario,
            "prioridad": prioridad,
            "archivada": archivada,
        }
        # Es un simple cambio de estado si pidieron "hecho" y ningún otro campo.
        solo_estado = hecho is not None and all(v is None for v in campos.values())

        # Si no es un simple cambio de estado, se exige ser autor o admin.
        if not solo_estado and not self._puede_editar(nota, usuario):
            raise ForbiddenError("Solo el autor o un administrador pueden editarla.")

        # Se aplican los cambios enviados uno por uno.
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
        """Elimina una nota si el usuario tiene permiso.

        Parámetros:
            nota_id: id de la nota a eliminar.
            usuario: usuario que solicita el borrado.

        Lanza:
            NotFoundError: si no existe.
            ForbiddenError: si no es el autor ni un administrador.
        """
        nota = self.obtener(nota_id)
        # Misma regla de permisos que para editar.
        if not self._puede_editar(nota, usuario):
            raise ForbiddenError("Solo el autor o un administrador pueden eliminarla.")
        self.notas.delete(nota_id)
        self.session.commit()
        event_bus.publish("nota_eliminada", {"id": nota_id})
