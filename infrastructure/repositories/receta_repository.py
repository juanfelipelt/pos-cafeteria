"""Repositorio SQLAlchemy para las recetas.

Implementa `RecetaRepository` del dominio sobre la tabla `receta_detalles`.
Una receta es el conjunto de componentes (insumos u otros productos) que
forman un producto preparado.
"""

from sqlalchemy.orm import Session

from domain.entities.detalle_receta import DetalleReceta
from domain.repositories.receta_repository import RecetaRepository
from infrastructure.models.receta import RecetaModel


def _to_entity(m: RecetaModel) -> DetalleReceta:
    """Convierte un modelo ORM `RecetaModel` en la entidad `DetalleReceta`."""
    return DetalleReceta(
        id=m.id,
        producto_id=m.producto_id,
        tipo=m.tipo,
        insumo_id=m.insumo_id or None,          # "" se normaliza a None.
        componente_producto_id=m.componente_producto_id,
        cantidad=m.cantidad,
    )


class SQLAlchemyRecetaRepository(RecetaRepository):
    """Implementación concreta de `RecetaRepository` con SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_by_producto(self, producto_id: str) -> list[DetalleReceta]:
        """Devuelve todos los componentes de la receta de un producto."""
        rows = (
            self.session.query(RecetaModel)
            .filter(RecetaModel.producto_id == producto_id)
            .all()
        )
        return [_to_entity(m) for m in rows]

    def list_all(self) -> list[DetalleReceta]:
        """Devuelve todos los componentes de todas las recetas."""
        return [_to_entity(m) for m in self.session.query(RecetaModel).all()]

    def set_for_producto(
        self, producto_id: str, detalles: list[DetalleReceta]
    ) -> list[DetalleReceta]:
        """Reemplaza por completo la receta de un producto.

        Borra los componentes actuales e inserta los nuevos; luego devuelve
        la receta ya guardada (releída desde la base de datos).
        """
        # Borrado de la receta anterior (patrón "borrar y reinsertar").
        self.session.query(RecetaModel).filter(
            RecetaModel.producto_id == producto_id
        ).delete(synchronize_session=False)
        # Inserción de los nuevos componentes.
        for detalle in detalles:
            self.session.add(
                RecetaModel(
                    id=detalle.id,
                    producto_id=producto_id,
                    tipo=detalle.tipo,
                    insumo_id=detalle.insumo_id or "",
                    componente_producto_id=detalle.componente_producto_id,
                    cantidad=detalle.cantidad,
                )
            )
        self.session.flush()
        # Releemos para devolver el estado real persistido.
        return self.list_by_producto(producto_id)

    def delete_by_producto(self, producto_id: str) -> None:
        """Elimina toda la receta de un producto."""
        self.session.query(RecetaModel).filter(
            RecetaModel.producto_id == producto_id
        ).delete(synchronize_session=False)
        self.session.flush()

    def has_for_insumo(self, insumo_id: str) -> bool:
        """Indica si un insumo se usa en alguna receta."""
        return (
            self.session.query(RecetaModel)
            .filter(RecetaModel.insumo_id == insumo_id)
            .first()
            is not None
        )
