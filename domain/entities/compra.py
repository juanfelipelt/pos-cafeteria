"""Entidad de dominio ``Compra``.

Representa la compra de mercancía a un proveedor. Es una "cabecera" que
agrupa varios ``DetalleCompra`` (cada línea indica qué producto o insumo se
compró, cuánta cantidad y a qué precio).

Invariantes del negocio:
- Toda compra debe tener un proveedor.
- Toda compra debe tener al menos una línea (detalle).
- El ``total`` es la suma de los subtotales de sus líneas.
- Una compra anulada no puede volver a anularse.
"""

from dataclasses import dataclass, field
from datetime import datetime

from .detalle_compra import DetalleCompra


@dataclass
class Compra:
    """Cabecera de una compra a proveedor con su lista de detalles."""

    # Proveedor al que se le compró. Obligatorio.
    proveedor_id: str
    # Líneas de la compra. ``default_factory=list`` crea una lista nueva por
    # cada compra (evita compartir la misma lista entre objetos).
    detalles: list[DetalleCompra] = field(default_factory=list)
    # Identificador único; None mientras no se haya persistido.
    id: str | None = None
    # Fecha de la compra; por defecto, el momento de creación.
    fecha: datetime = field(default_factory=datetime.now)
    # Indica si la compra fue anulada (no cuenta para los cálculos).
    anulada: bool = False

    def __post_init__(self) -> None:
        """Valida las invariantes al construir la compra."""
        # Debe estar asociada a un proveedor.
        if not self.proveedor_id:
            raise ValueError("El proveedor es obligatorio.")

        # Una compra sin líneas no tiene sentido de negocio.
        if not self.detalles:
            raise ValueError("La compra debe tener al menos un detalle.")

    @property
    def total(self) -> float:
        """Suma de los subtotales de todas las líneas de la compra."""
        return sum(detalle.subtotal for detalle in self.detalles)

    def agregar_detalle(self, detalle: DetalleCompra) -> None:
        """Añade una nueva línea (producto o insumo) a la compra."""
        self.detalles.append(detalle)

    def anular(self) -> None:
        """Anula la compra. No permite anular una que ya estaba anulada."""
        if self.anulada:
            raise ValueError("La compra ya está anulada.")
        self.anulada = True

    def to_dict(self) -> dict:
        """Convierte la compra (con sus líneas) a un diccionario serializable."""
        return {
            "id": self.id,
            "proveedor_id": self.proveedor_id,
            # ``isoformat()`` pasa la fecha a texto estándar (AAAA-MM-DD...).
            "fecha": self.fecha.isoformat(),
            # Se serializa cada detalle con su propio ``to_dict``.
            "detalles": [detalle.to_dict() for detalle in self.detalles],
            "total": self.total,
            "anulada": self.anulada,
        }
