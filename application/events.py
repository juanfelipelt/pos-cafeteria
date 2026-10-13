"""Bus de eventos en memoria (patrón pub/sub) para notificaciones en tiempo real.

Permite que distintas partes de la aplicación **publiquen** eventos (por ejemplo,
"se creó una venta") y que los clientes **suscriptos** los reciban al instante.
Se usa para Server-Sent Events (SSE): el frontend abre una conexión y va
recibiendo los eventos conforme ocurren, sin recargar la página.

Importante: es un bus **en memoria**, por lo que los eventos se pierden al
reiniciar y no se comparten entre varios procesos/servidores.

Se relaciona con los routers de ``eventos`` (que exponen el stream SSE) y con
los servicios que llaman a ``event_bus.publish(...)`` cuando algo relevante pasa.
"""

import asyncio
from typing import Any


class EventBus:
    """Bus pub/sub en memoria para eventos de tiempo real (SSE)."""

    def __init__(self) -> None:
        """Inicializa el bus sin suscriptores y sin bucle de eventos asignado."""
        # Lista de colas: cada suscriptor (cliente conectado) tiene la suya.
        self._subscribers: list[asyncio.Queue] = []
        # Bucle de eventos de asyncio, necesario para publicar de forma segura
        # desde otros hilos (call_soon_threadsafe).
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Guarda el bucle de eventos que usará ``publish``.

        Se llama normalmente al arrancar la aplicación.

        Parámetros:
            loop (asyncio.AbstractEventLoop): bucle de eventos en ejecución.

        Retorno:
            None
        """
        self._loop = loop

    def subscribe(self) -> asyncio.Queue:
        """Registra un nuevo suscriptor y devuelve su cola de mensajes.

        Retorno:
            asyncio.Queue: cola donde ese suscriptor recibirá los eventos.
        """
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        """Elimina un suscriptor (cuando el cliente se desconecta).

        Parámetros:
            queue (asyncio.Queue): cola del suscriptor a eliminar.

        Retorno:
            None
        """
        # Solo se elimina si realmente estaba suscrito (evita errores).
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    def publish(self, event_type: str, data: Any) -> None:
        """Publica un evento a todos los suscriptores actuales.

        Parámetros:
            event_type (str): nombre/tipo del evento (p. ej. "venta_creada").
            data (Any): información asociada al evento (debe ser serializable).

        Retorno:
            None
        """
        # Si no hay bucle activo, no hay forma segura de entregar el evento.
        if self._loop is None or self._loop.is_closed():
            return
        # Mensaje estándar que recibe el frontend.
        message = {"type": event_type, "data": data}
        for queue in self._subscribers:
            # call_soon_threadsafe permite publicar desde hilos distintos al
            # del bucle de eventos sin corromper las colas de asyncio.
            self._loop.call_soon_threadsafe(self._enqueue, queue, message)

    def _enqueue(self, queue: asyncio.Queue, message: dict) -> None:
        """Coloca un mensaje en la cola de un suscriptor (uso interno).

        Parámetros:
            queue (asyncio.Queue): cola destino.
            message (dict): mensaje a encolar.

        Retorno:
            None
        """
        try:
            # put_nowait no bloquea; si la cola está llena lanzaría excepción.
            queue.put_nowait(message)
        except Exception:
            # Si la cola está llena o cerrada, se ignora el evento para no
            # interrumpir al resto de suscriptores.
            pass


# Instancia única (singleton) del bus que importa el resto de la aplicación.
event_bus = EventBus()
