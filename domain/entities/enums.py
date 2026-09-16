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


class TipoProducto(str, Enum):
    """Cómo se costea el producto.

    - COMPRADO: se compra terminado a proveedor y se revende (costo = compras).
    - PREPARADO: se elabora a partir de insumos (costo = receta de insumos).
    - COMPUESTO: combo de otros productos y/o insumos (costo = sus componentes).
    """

    COMPRADO = "comprado"
    PREPARADO = "preparado"
    COMPUESTO = "compuesto"


class TipoComponente(str, Enum):
    """Tipo de componente dentro de una receta."""

    INSUMO = "insumo"
    PRODUCTO = "producto"


class TipoLineaCompra(str, Enum):
    """Tipo de línea dentro de una compra a proveedor."""

    PRODUCTO = "producto"
    INSUMO = "insumo"


class TipoNota(str, Enum):
    """Tipo de ítem de la pizarra."""

    TAREA = "tarea"
    NOTA = "nota"


class DestinatarioNota(str, Enum):
    """A quién va dirigida una nota/tarea."""

    TODOS = "todos"
    ADMIN = "admin"
    CAJERO = "cajero"


class PrioridadNota(str, Enum):
    NORMAL = "normal"
    ALTA = "alta"
