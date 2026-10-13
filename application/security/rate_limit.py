"""Seguridad: límite de peticiones (rate limiting).

Sirve para evitar abusos como intentar adivinar contraseñas o saturar la API.
Limita cuántas veces se puede llamar a una acción (por ejemplo, login) dentro
de una ventana de tiempo, contando por una clave (email, IP, etc.).

La implementación es simple y en memoria: guarda en un diccionario las marcas
de tiempo de los intentos recientes. Es ideal para un entorno pequeño; en un
sistema distribuido se reemplazaría por un almacén compartido (por ejemplo
Redis).

Relación con el resto:
- `login_limiter` es una instancia lista para usarse en el flujo de login.
"""

import time
from collections import defaultdict


class RateLimiter:
    """Limitador simple en memoria por clave (p. ej. email o IP)."""

    def __init__(self, max_attempts: int = 10, window_seconds: int = 300) -> None:
        """Configura el límite.

        `max_attempts`: número máximo de intentos permitidos.
        `window_seconds`: duración de la ventana de tiempo, en segundos.
        """
        self.max_attempts = max_attempts
        self.window = window_seconds
        # Diccionario clave -> lista de marcas de tiempo de los intentos.
        # defaultdict(list) crea la lista vacía automáticamente al consultar.
        self._attempts: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str) -> bool:
        """Indica si la petición de `key` se permite según el límite.

        Devuelve True si aún está dentro del cupo y registra el intento;
        devuelve False si ya se superó el máximo en la ventana actual.
        """
        # Momento actual.
        now = time.time()
        # Conservamos solo los intentos dentro de la ventana de tiempo.
        recent = [t for t in self._attempts[key] if now - t < self.window]
        self._attempts[key] = recent
        # Si ya se alcanzó el máximo, bloqueamos (sin registrar el intento).
        if len(recent) >= self.max_attempts:
            return False
        # Si hay cupo, registramos este intento y lo permitimos.
        recent.append(now)
        return True

    def reset(self, key: str) -> None:
        """Borra el historial de intentos de `key`.

        Útil, por ejemplo, tras un login exitoso para reiniciar el contador.
        """
        self._attempts.pop(key, None)


# Instancia compartida: 10 intentos cada 5 minutos (300 segundos).
login_limiter = RateLimiter(max_attempts=10, window_seconds=300)
