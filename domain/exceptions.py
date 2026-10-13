"""Excepciones propias del dominio del negocio.

En lugar de lanzar errores genéricos de Python por toda la aplicación,
definimos nuestros propios tipos de error. Así cada capa sabe *qué* salió mal
(el recurso no existe, los datos son inválidos, hay un conflicto...) y puede
reaccionar de forma adecuada (por ejemplo, traducirlo al código de estado HTTP
correcto en la capa web).

Todas las excepciones heredan de ``DomainError``, así que atrapando ese tipo
base se capturan todos los errores de negocio a la vez.
"""


class DomainError(Exception):
    """Error base del dominio.

    Sirve como "paraguas": toda excepción de negocio hereda de aquí, lo que
    permite capturar cualquiera de ellas con un solo ``except DomainError``.
    """


class NotFoundError(DomainError):
    """Se lanza cuando el recurso solicitado no existe (por ejemplo, un id
    desconocido). Se traduce normalmente a un HTTP 404.
    """


class ValidationError(DomainError):
    """Se lanza cuando los datos de entrada son inválidos (campos vacíos,
    valores negativos, formatos incorrectos...). Se traduce a un HTTP 400.
    """


class ConflictError(DomainError):
    """Se lanza cuando la operación choca con el estado actual, por ejemplo al
    intentar crear un usuario con un email que ya existe. Suele ser un HTTP 409.
    """


class ForbiddenError(DomainError):
    """Se lanza cuando el usuario está identificado pero no tiene permisos para
    realizar la acción. Se traduce a un HTTP 403.
    """


class UnauthorizedError(DomainError):
    """Se lanza cuando las credenciales son inválidas o falta el token de
    autenticación. Se traduce a un HTTP 401.
    """
