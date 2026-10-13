"""Entidad de dominio ``Pago``.

Representa un pago aplicado a una venta. Una venta puede tener varios pagos
(por ejemplo, parte en efectivo y parte con tarjeta), por eso el pago es una
entidad aparte y no un simple campo de la venta.

Invariantes del negocio:
- El monto debe ser mayor que cero.
- El método debe ser uno de los permitidos por ``MetodoPago``.
"""

from dataclasses import dataclass, field
from datetime import datetime

from .enums import MetodoPago


@dataclass
class Pago:
    """Pago asociado a una venta."""

    # Dinero entregado en este pago (> 0).
    monto: float
    # Cómo se pagó: efectivo, tarjeta o transferencia.
    metodo: MetodoPago
    # Identificador único; None mientras no se haya guardado.
    id: str | None = None
    # Momento en que se registró el pago.
    fecha: datetime = field(default_factory=datetime.now)
    # Número de comprobante, aprobación, etc. (opcional).
    referencia: str | None = None

    def __post_init__(self) -> None:
        """Valida el método de pago y el monto al crear el pago."""
        # El método puede llegar como texto (por ejemplo desde una API) y aquí
        # se convierte al enum. Si el texto no corresponde a ningún método
        # conocido, ``MetodoPago(...)`` lanza ValueError y lo reportamos.
        if isinstance(self.metodo, str):
            try:
                self.metodo = MetodoPago(self.metodo)
            except ValueError:
                raise ValueError(f"Método de pago no válido: {self.metodo}")

        # Un pago de cero o negativo no tiene sentido.
        if self.monto <= 0:
            raise ValueError("El monto del pago debe ser mayor que cero.")

    def to_dict(self) -> dict:
        """Serializa el pago a un diccionario."""
        return {
            "id": self.id,
            "monto": self.monto,
            # ``.value`` devuelve el texto del enum ("efectivo", "tarjeta"...).
            "metodo": self.metodo.value,
            "fecha": self.fecha.isoformat(),
            "referencia": self.referencia,
        }
