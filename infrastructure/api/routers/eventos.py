"""
Router de eventos en tiempo real (Server-Sent Events / SSE).

Recurso que expone: un canal de notificaciones en vivo. El cliente abre una
conexión y el servidor le va enviando mensajes cuando ocurren cosas en el
sistema (nuevas ventas, cambios, etc.), sin que el cliente tenga que
preguntar constantemente.

Prefijo base de las rutas: `/eventos`

Endpoints:
- GET /eventos/stream -> conexión de flujo continuo de eventos (SSE).

Nivel de acceso: requiere un token válido, que se pasa como parámetro de
consulta (`?token=...`) porque los navegadores no permiten encabezados
personalizados fácilmente en este tipo de conexión.
"""

import asyncio
import json

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import jwt

from application.events import event_bus
from application.security.jwt import decode_token

# Router con prefijo "/eventos".
router = APIRouter(prefix="/eventos", tags=["eventos"])


@router.get("/stream")
async def stream(token: str = Query(...)):
    """
    Abre un flujo (stream) de eventos para el usuario autenticado.

    Parámetros:
        token: Token JWT enviado en la URL como `?token=...`. FastAPI lo
               marca como obligatorio con `Query(...)`.

    Respuesta:
        Un `StreamingResponse` de tipo `text/event-stream` que envía eventos
        con el formato SSE (`data: ...`) y mensajes de "ping" para mantener
        viva la conexión.

    Nivel de acceso:
        Requiere token válido; si no, responde HTTP 401.
    """
    try:
        # Verificamos el token antes de aceptar la conexión.
        decode_token(token)
    except jwt.PyJWTError:
        # Token inválido o expirado: no abrimos el stream.
        raise HTTPException(status_code=401, detail="Token inválido o expirado.")

    # Nos suscribimos al bus de eventos: creamos una cola donde llegarán los
    # mensajes que el sistema publique.
    queue = event_bus.subscribe()
    # Registramos el bucle de asyncio actual para que otras partes del sistema
    # puedan publicar eventos en esta cola de forma segura desde otro hilo.
    event_bus.set_loop(asyncio.get_running_loop())

    async def generar():
        """
        Generador asíncrono que produce el contenido del stream.

        Se ejecuta de forma continua mientras el cliente siga conectado.
        """
        try:
            while True:
                try:
                    # Esperamos un mensaje nuevo hasta 15 segundos.
                    message = await asyncio.wait_for(queue.get(), timeout=15.0)
                    # Formato SSE: "data: <json>" seguido de dos saltos de línea.
                    yield f"data: {json.dumps(message, default=str)}\n\n"
                except asyncio.TimeoutError:
                    # Si no hay mensajes en 15s, enviamos un comentario "ping"
                    # (las líneas que empiezan con ":" son ignoradas por el
                    # cliente pero mantienen viva la conexión).
                    yield ": ping\n\n"
        finally:
            # Pase lo que pase, al cerrar la conexión nos desuscribimos para
            # no dejar colas "colgadas" consumiendo memoria.
            event_bus.unsubscribe(queue)

    return StreamingResponse(generar(), media_type="text/event-stream")
