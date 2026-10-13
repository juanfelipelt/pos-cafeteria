"""Entidad de dominio ``Venta``.

Representa una venta realizada en el punto de venta. Es una "cabecera" que
agrupa los productos vendidos (``DetalleVenta``) y los pagos recibidos
(``Pago``). A partir de ellos se calculan el total, lo pagado y lo que queda
pendiente.

Invariantes del negocio:
- Toda venta debe tener al menos un detalle (no se vende "nada").
- No se puede registrar un pago si la venta está anulada.
- Un pago no puede exceder el total de la venta.
- Una venta anulada no puede volver a anularse.
"""

from dataclasses import dataclass, field
from datetime import datetime

from .detalle_venta import DetalleVenta
from .pago import Pago


@dataclass
class Venta:
    """Entidad de dominio para una venta en el sistema."""

    # Productos vendidos. Lista propia por venta (default_factory).
    detalles: list[DetalleVenta] = field(default_factory=list)
    # Identificador único; None mientras no se haya guardado.
    id: str | None = None
    # Usuario (cajero) que registró la venta.
    usuario_id: str | None = None
    # Fecha y hora de la venta; por defecto, el momento de creación.
    fecha: datetime = field(default_factory=datetime.now)
    # Pagos aplicados a esta venta (puede haber varios).
    pagos: list[Pago] = field(default_factory=list)
    # Indica si la venta fue anulada.
    anulada: bool = False

    def __post_init__(self) -> None:
        """Valida que la venta tenga al menos un producto."""
        # Una venta sin líneas no representa ninguna operación real.
        if not self.detalles:
            raise ValueError("La venta debe tener al menos un detalle.")

    @property
    def total(self) -> float:
        """Valor total de la venta: suma de los subtotales de cada línea."""
        return sum(detalle.subtotal for detalle in self.detalles)

    @property
    def total_pagado(self) -> float:
        """Suma de todos los pagos recibidos para esta venta."""
        return sum(pago.monto for pago in self.pagos)

    @property
    def pendiente(self) -> float:
        """Saldo que aún falta por pagar.

        Se usa ``max(0.0, ...)`` para evitar negativos por pequeños errores de
        redondeo con decimales.
        """
        return max(0.0, self.total - self.total_pagado)

    @property
    def esta_pagada(self) -> bool:
        """Indica si lo pagado cubre (o supera) el total de la venta."""
        return self.total_pagado >= self.total

    def agregar_detalle(self, detalle: DetalleVenta) -> None:
        """Añade un producto vendido a la venta."""
        self.detalles.append(detalle)

    def registrar_pago(self, pago: Pago) -> None:
        """Registra un pago aplicando las reglas de negocio de la venta."""
        # No se puede cobrar una venta que fue anulada.
        if self.anulada:
            raise ValueError("No se puede registrar un pago a una venta anulada.")
        # El monto debe ser positivo (cada Pago ya lo valida, se refuerza aquí).
        if pago.monto <= 0:
            raise ValueError("El monto del pago debe ser mayor que cero.")
        # No se permite pagar más de lo que vale la venta.
        if self.total_pagado + pago.monto > self.total:
            raise ValueError("El pago excede el total de la venta.")
        self.pagos.append(pago)

    def anular(self) -> None:
        """Anula la venta. No permite anular una que ya estaba anulada."""
        if self.anulada:
            raise ValueError("La venta ya está anulada.")
        self.anulada = True

    def to_dict(self) -> dict:
        """Serializa la venta (con líneas y pagos) a un diccionario.

        Incluye los valores calculados (total, total_pagado, pendiente...)
        para que el cliente de la API no tenga que recalcularlos.
        """
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "fecha": self.fecha.isoformat(),
            "detalles": [detalle.to_dict() for detalle in self.detalles],
            "pagos": [pago.to_dict() for pago in self.pagos],
            "total": self.total,
            "total_pagado": self.total_pagado,
            "pendiente": self.pendiente,
            "esta_pagada": self.esta_pagada,
            "anulada": self.anulada,
        }
