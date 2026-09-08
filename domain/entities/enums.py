from enum import Enum


class MetodoPago(str, Enum):
    EFECTIVO = "efectivo"
    TARJETA = "tarjeta"
    TRANSFERENCIA = "transferencia"


class Rol(str, Enum):
    ADMIN = "admin"
    CAJERO = "cajero"


class TipoIdentificacion(str, Enum):
    CC = "CC"
    NIT = "NIT"
    CE = "CE"
    TI = "TI"
    PPT = "PPT"
    PASAPORTE = "PASAPORTE"
    OTRO = "OTRO"
