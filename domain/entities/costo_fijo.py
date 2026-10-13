"""Entidad de dominio ``CostoFijo``.

Un costo fijo es un gasto que se repite cada mes y no depende de cuánto se
venda: arriendo, servicios, sueldos, etc. Se usa para calcular cuánto cuesta
mantener el negocio funcionando.

Invariantes del negocio:
- El nombre es obligatorio (para identificar el gasto).
- El monto nunca puede ser negativo.
"""

from dataclasses import dataclass


@dataclass
class CostoFijo:
    """Gasto mensual recurrente del negocio (arriendo, servicios, etc.)."""

    # Nombre que identifica el gasto (obligatorio).
    nombre: str
    # Valor mensual en dinero. No puede ser negativo.
    monto: float = 0.0
    # Identificador único; None mientras no se haya guardado.
    id: str | None = None
    # Indica si el costo sigue vigente (True) o fue desactivado (False).
    activo: bool = True

    def __post_init__(self) -> None:
        """Normaliza y valida los datos al crear el costo fijo."""
        # Limpia espacios; si el campo venía vacío, deja cadena vacía.
        self.nombre = self.nombre.strip() if self.nombre else ""
        if not self.nombre:
            raise ValueError("El nombre del costo fijo es obligatorio.")
        # Un costo negativo indicaría un ingreso, lo cual no tiene sentido aquí.
        if self.monto < 0:
            raise ValueError("El monto del costo fijo no puede ser negativo.")

    def cambiar_nombre(self, nuevo_nombre: str) -> None:
        """Cambia el nombre del costo fijo validando que no quede vacío."""
        if not nuevo_nombre or not nuevo_nombre.strip():
            raise ValueError("El nombre del costo fijo no puede estar vacío.")
        self.nombre = nuevo_nombre.strip()

    def cambiar_monto(self, nuevo_monto: float) -> None:
        """Actualiza el monto, impidiendo valores negativos."""
        if nuevo_monto < 0:
            raise ValueError("El monto del costo fijo no puede ser negativo.")
        self.monto = nuevo_monto

    def activar(self) -> None:
        """Marca el costo fijo como vigente."""
        self.activo = True

    def desactivar(self) -> None:
        """Marca el costo fijo como no vigente (ya no se cuenta)."""
        self.activo = False

    def to_dict(self) -> dict:
        """Serializa el costo fijo a un diccionario."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "monto": self.monto,
            "activo": self.activo,
        }
