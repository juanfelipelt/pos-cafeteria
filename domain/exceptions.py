class DomainError(Exception):
    """Error base de dominio."""


class NotFoundError(DomainError):
    """El recurso no existe."""


class ValidationError(DomainError):
    """Datos de entrada inválidos."""


class ConflictError(DomainError):
    """Conflicto de estado (p. ej. email duplicado)."""


class ForbiddenError(DomainError):
    """El usuario no tiene permisos."""


class UnauthorizedError(DomainError):
    """Credenciales inválidas o token ausente."""
