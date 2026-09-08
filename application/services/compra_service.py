from sqlalchemy.orm import Session

from application.utils import new_id
from domain.entities.compra import Compra
from domain.entities.detalle_compra import DetalleCompra
from domain.exceptions import NotFoundError, ValidationError
from domain.repositories.compra_repository import CompraRepository
from domain.repositories.producto_repository import ProductoRepository


class CompraService:
    def __init__(
        self,
        compras: CompraRepository,
        productos: ProductoRepository,
        session: Session,
    ) -> None:
        self.compras = compras
        self.productos = productos
        self.session = session

    def crear(self, proveedor_id: str, items: list[dict]) -> Compra:
        if not items:
            raise ValidationError("La compra debe tener al menos un producto.")

        detalles: list[DetalleCompra] = []
        for item in items:
            producto = self.productos.get(item["producto_id"])
            if producto is None:
                raise NotFoundError(f"Producto no encontrado: {item['producto_id']}")

            cantidad = item["cantidad"]
            precio_unitario = item["precio_unitario"]
            detalles.append(
                DetalleCompra(
                    id=new_id(),
                    producto_id=producto.id,
                    nombre_producto=producto.nombre,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                )
            )
            producto.stock += cantidad
            self.productos.update(producto)

        compra = Compra(id=new_id(), proveedor_id=proveedor_id, detalles=detalles)
        self.compras.add(compra)
        self.session.commit()
        return compra

    def listar(self, desde=None, hasta=None) -> list[Compra]:
        return self.compras.list(desde, hasta)

    def obtener(self, compra_id: str) -> Compra:
        compra = self.compras.get(compra_id)
        if compra is None:
            raise NotFoundError("Compra no encontrada.")
        return compra

    def anular(self, compra_id: str) -> Compra:
        compra = self.obtener(compra_id)
        compra.anular()

        for detalle in compra.detalles:
            producto = self.productos.get(detalle.producto_id)
            if producto is not None:
                if producto.stock < detalle.cantidad:
                    raise ValidationError(
                        f"No se puede anular: stock insuficiente de "
                        f"'{producto.nombre}'."
                    )
                producto.stock -= detalle.cantidad
                self.productos.update(producto)

        self.compras.update(compra)
        self.session.commit()
        return compra

    def eliminar(self, compra_id: str) -> None:
        compra = self.obtener(compra_id)

        if not compra.anulada:
            for detalle in compra.detalles:
                producto = self.productos.get(detalle.producto_id)
                if producto is not None:
                    if producto.stock < detalle.cantidad:
                        raise ValidationError(
                            f"No se puede eliminar: stock insuficiente de "
                            f"'{producto.nombre}'."
                        )
                    producto.stock -= detalle.cantidad
                    self.productos.update(producto)

        self.compras.delete(compra.id)
        self.session.commit()
