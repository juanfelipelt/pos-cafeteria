"""Schemas (DTOs) de ventas y pagos.

Aquí se describen los datos que entran/salen al registrar una venta: los
productos vendidos, sus cantidades y los pagos realizados (con su método).

Son DTOs: solo validan y transportan datos; el cálculo de totales o vueltas se
resuelve en los casos de uso.

Nota: `MetodoPago` es un enumerado del dominio que limita los métodos de pago
válidos.
"""

from pydantic import BaseModel

from domain.entities.enums import MetodoPago


class ItemVenta(BaseModel):
    """Un producto vendido dentro de una venta."""

    # Identificador del producto vendido.
    producto_id: str
    # Cantidad vendida (entero).
    cantidad: int


class PagoInput(BaseModel):
    """Un pago asociado a la venta."""

    # Monto pagado.
    monto: float
    # Método de pago (efectivo, tarjeta, etc.), restringido por el enum.
    metodo: MetodoPago
    # Referencia opcional (número de transacción, etc.).
    referencia: str | None = None


class VentaCreate(BaseModel):
    """Datos para registrar una venta."""

    # Productos vendidos.
    items: list[ItemVenta]
    # Pagos realizados; por defecto lista vacía.
    pagos: list[PagoInput] = []


class PagoCreate(BaseModel):
    """Datos para registrar un pago suelto."""

    # Monto pagado.
    monto: float
    # Método de pago, restringido por el enum.
    metodo: MetodoPago
    # Referencia opcional del pago.
    referencia: str | None = None
