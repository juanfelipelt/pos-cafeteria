import time
from collections import defaultdict


class RateLimiter:
    """Limitador simple en memoria por clave (p. ej. email o IP)."""

    def __init__(self, max_attempts: int = 10, window_seconds: int = 300) -> None:
        self.max_attempts = max_attempts
        self.window = window_seconds
        self._attempts: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str) -> bool:
        now = time.time()
        recent = [t for t in self._attempts[key] if now - t < self.window]
        self._attempts[key] = recent
        if len(recent) >= self.max_attempts:
            return False
        recent.append(now)
        return True

    def reset(self, key: str) -> None:
        self._attempts.pop(key, None)


login_limiter = RateLimiter(max_attempts=10, window_seconds=300)
