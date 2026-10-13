"""Enumeraciones (enums) del dominio del negocio.

Un *enum* es una lista cerrada de valores válidos: en vez de aceptar cualquier
texto (por ejemplo "efectivo", "Efectivo" o "efectivo "), limitamos las
opciones a un conjunto fijo y conocido. Así evitamos errores de escritura y
centralizamos en un solo lugar los valores permitidos.

Cada enum hereda de ``str`` y ``Enum`` al mismo tiempo. Por eso cada valor se
comporta como una cadena (se puede comparar con texto o guardar en la base de
datos) pero conserva las ventajas de un enumerado (todos los valores posibles
están declarados aquí).
"""

from enum import Enum


class MetodoPago(str, Enum):
    """Formas de pago aceptadas al registrar una venta."""

    # Dinero en efectivo entregado en caja.
    EFECTIVO = "efectivo"
    # Pago con tarjeta débito o crédito.
    TARJETA = "tarjeta"
    # Pago por transferencia bancaria.
    TRANSFERENCIA = "transferencia"


class Rol(str, Enum):
    """Roles (perfiles) que puede tener un usuario del sistema.

    El rol determina qué acciones están permitidas: un ADMIN administra todo
    el negocio, mientras que un CAJERO se dedica a registrar ventas.
    """

    # Administrador: acceso total a la configuración y reportes.
    ADMIN = "admin"
    # Cajero: perfil operativo para atender el punto de venta.
    CAJERO = "cajero"


class TipoIdentificacion(str, Enum):
    """Tipos de documento de identidad válidos para personas o empresas."""

    CC = "CC"  # Cédula de ciudadanía.
    NIT = "NIT"  # Número de identificación tributaria (empresas).
    CE = "CE"  # Cédula de extranjería.
    TI = "TI"  # Tarjeta de identidad (menores de edad).
    PPT = "PPT"  # Permiso por protección temporal.
    PASAPORTE = "PASAPORTE"  # Pasaporte.
    OTRO = "OTRO"  # Cualquier otro documento no listado.


class TipoProducto(str, Enum):
    """Cómo se costea el producto.

    - COMPRADO: se compra terminado a proveedor y se revende (costo = compras).
    - PREPARADO: se elabora a partir de insumos (costo = receta de insumos).
    - COMPUESTO: combo de otros productos y/o insumos (costo = sus componentes).
    """

    # Se compra ya terminado a un proveedor y solo se revende.
    COMPRADO = "comprado"
    # Se elabora en el negocio a partir de insumos (tiene receta).
    PREPARADO = "preparado"
    # Es un combo formado por otros productos y/o insumos.
    COMPUESTO = "compuesto"


class TipoComponente(str, Enum):
    """Tipo de componente dentro de una receta.

    Sirve para saber si un producto se prepara con materia prima (insumo) o si
    es un combo que incluye otro producto ya existente.
    """

    INSUMO = "insumo"  # El componente es materia prima.
    PRODUCTO = "producto"  # El componente es otro producto (combo).


class TipoLineaCompra(str, Enum):
    """Tipo de línea dentro de una compra a proveedor.

    Una compra puede mezclar productos terminados e insumos; este enum indica
    qué clase de artículo se está comprando en cada línea.
    """

    PRODUCTO = "producto"  # La línea compra un producto terminado.
    INSUMO = "insumo"  # La línea compra materia prima.


class TipoNota(str, Enum):
    """Tipo de ítem de la pizarra.

    Distingue una simple nota informativa de una tarea que debe completarse.
    """

    TAREA = "tarea"  # Tiene estado pendiente/hecho.
    NOTA = "nota"  # Es solo un mensaje, sin estado de completado.


class DestinatarioNota(str, Enum):
    """A quién va dirigida una nota/tarea."""

    TODOS = "todos"  # Visible para todo el equipo.
    ADMIN = "admin"  # Dirigida solo a los administradores.
    CAJERO = "cajero"  # Dirigida solo a los cajeros.


class PrioridadNota(str, Enum):
    """Nivel de urgencia de una nota/tarea de la pizarra."""

    NORMAL = "normal"  # Prioridad por defecto.
    ALTA = "alta"  # Requiere atención inmediata.
