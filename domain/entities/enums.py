from enum import Enum


class MetodoPago(str, Enum):
    EFECTIVO = "efectivo"
    TARJETA = "tarjeta"
    TRANSFERENCIA = "transferencia"


class Rol(str, Enum):
    ADMIN = "admin"
    CAJERO = "cajero"
