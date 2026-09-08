from dataclasses import dataclass, field
from datetime import datetime

from .enums import MetodoPago


@dataclass
class Pago:
    """Pago asociado a una venta."""

    monto: float
    metodo: MetodoPago
    id: str | None = None
    fecha: datetime = field(default_factory=datetime.now)
    referencia: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.metodo, str):
            try:
                self.metodo = MetodoPago(self.metodo)
            except ValueError:
                raise ValueError(f"Método de pago no válido: {self.metodo}")

        if self.monto <= 0:
            raise ValueError("El monto del pago debe ser mayor que cero.")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "monto": self.monto,
            "metodo": self.metodo.value,
            "fecha": self.fecha.isoformat(),
            "referencia": self.referencia,
        }
