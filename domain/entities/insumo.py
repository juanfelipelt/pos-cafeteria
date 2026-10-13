"""Entidad de dominio ``Insumo``.

Un insumo es la **materia prima** con la que se preparan los productos
(harina, queso, carne, bebidas base...). A diferencia de un producto, no se
vende directamente: se consume en las recetas.

Invariantes del negocio:
- El nombre y la unidad de medida son obligatorios (no se puede hablar de
  "harina" sin saber si son gramos, kilos o libras).
- El stock y el costo unitario nunca pueden ser negativos.
"""

from dataclasses import dataclass


@dataclass
class Insumo:
    """Entidad de dominio para un insumo (materia prima)."""

    # Identificador único; None mientras no se haya guardado.
    id: str | None = None
    # Nombre del insumo (obligatorio).
    nombre: str = ""
    # Unidad de medida: "kg", "g", "lt", "unidad"... (obligatoria).
    unidad: str = ""
    # Existencias disponibles en bodega.
    stock: float = 0.0
    # Valor de una unidad del insumo.
    costo_unitario: float = 0.0
    # Proveedor habitual del insumo (opcional).
    proveedor_id: str | None = None
    # Borrado lógico: True = habilitado, False = deshabilitado.
    estado: bool = True

    def __post_init__(self) -> None:
        """Normaliza el texto y valida las reglas al crear el insumo."""
        # Se limpian espacios en blanco de los campos de texto.
        self.nombre = self.nombre.strip() if self.nombre else ""
        self.unidad = self.unidad.strip() if self.unidad else ""
        # El proveedor es opcional: si viene vacío, se guarda None.
        self.proveedor_id = self.proveedor_id.strip() if self.proveedor_id else None

        if not self.nombre:
            raise ValueError("El nombre del insumo es obligatorio.")
        if not self.unidad:
            raise ValueError("La unidad del insumo es obligatoria.")
        # No puede existir stock negativo (indicaría datos corruptos).
        if self.stock < 0:
            raise ValueError("El stock del insumo no puede ser negativo.")
        # El costo es un valor monetario; nunca negativo.
        if self.costo_unitario < 0:
            raise ValueError("El costo del insumo no puede ser negativo.")

    def cambiar_nombre(self, nuevo_nombre: str) -> None:
        """Cambia el nombre del insumo validando que no quede vacío."""
        if not nuevo_nombre or not nuevo_nombre.strip():
            raise ValueError("El nombre del insumo no puede estar vacío.")
        self.nombre = nuevo_nombre.strip()

    def cambiar_unidad(self, nueva_unidad: str) -> None:
        """Cambia la unidad de medida validando que no quede vacía."""
        if not nueva_unidad or not nueva_unidad.strip():
            raise ValueError("La unidad del insumo no puede estar vacía.")
        self.unidad = nueva_unidad.strip()

    def cambiar_proveedor_id(self, nuevo_proveedor_id: str | None) -> None:
        """Asigna o quita el proveedor del insumo (acepta None)."""
        self.proveedor_id = (
            # Si no hay proveedor, se guarda None en lugar de cadena vacía.
            nuevo_proveedor_id.strip() if nuevo_proveedor_id else None
        )

    def desactivar(self) -> None:
        """Deshabilita el insumo sin borrarlo de la base de datos."""
        self.estado = False

    def activar(self) -> None:
        """Vuelve a habilitar el insumo."""
        self.estado = True

    def to_dict(self) -> dict:
        """Serializa el insumo a un diccionario."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "unidad": self.unidad,
            "stock": self.stock,
            "costo_unitario": self.costo_unitario,
            "proveedor_id": self.proveedor_id,
            "estado": self.estado,
        }
