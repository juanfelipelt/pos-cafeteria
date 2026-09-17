from sqlalchemy.orm import Session

from application.utils import new_id
from domain.entities.compra import Compra
from domain.entities.detalle_compra import DetalleCompra
from domain.entities.enums import TipoLineaCompra
from domain.exceptions import NotFoundError, ValidationError
from domain.repositories.compra_repository import CompraRepository
from domain.repositories.insumo_repository import InsumoRepository
from domain.repositories.producto_repository import ProductoRepository


def _promedio_ponderado(
    stock_actual: float, costo_actual: float, cantidad: float, precio: float
) -> float:
    total = stock_actual + cantidad
    if total <= 0:
        return precio
    return (stock_actual * costo_actual + cantidad * precio) / total


class CompraService:
    def __init__(
        self,
        compras: CompraRepository,
        productos: ProductoRepository,
        insumos: InsumoRepository,
        session: Session,
    ) -> None:
        self.compras = compras
        self.productos = productos
        self.insumos = insumos
        self.session = session

    def _aplicar_items(self, items: list[dict]) -> list[DetalleCompra]:
        """Aplica cada línea (sube stock y recalcula costo) y devuelve los
        detalles de dominio."""
        detalles: list[DetalleCompra] = []
        for item in items:
            tipo = item.get("tipo", TipoLineaCompra.PRODUCTO.value)
            cantidad = item["cantidad"]
            precio_unitario = item["precio_unitario"]

            if tipo == TipoLineaCompra.INSUMO.value:
                insumo = self.insumos.get(item["insumo_id"])
                if insumo is None:
                    raise NotFoundError(f"Insumo no encontrado: {item['insumo_id']}")
                insumo.costo_unitario = _promedio_ponderado(
                    insumo.stock, insumo.costo_unitario, cantidad, precio_unitario
                )
                insumo.stock += cantidad
                self.insumos.update(insumo)
                detalles.append(
                    DetalleCompra(
                        id=new_id(),
                        tipo=TipoLineaCompra.INSUMO.value,
                        insumo_id=insumo.id,
                        nombre_insumo=insumo.nombre,
                        cantidad=cantidad,
                        precio_unitario=precio_unitario,
                    )
                )
            else:
                producto = self.productos.get(item["producto_id"])
                if producto is None:
                    raise NotFoundError(
                        f"Producto no encontrado: {item['producto_id']}"
                    )
                producto.costo = _promedio_ponderado(
                    producto.stock, producto.costo, cantidad, precio_unitario
                )
                producto.stock += int(round(cantidad))
                self.productos.update(producto)
                detalles.append(
                    DetalleCompra(
                        id=new_id(),
                        tipo=TipoLineaCompra.PRODUCTO.value,
                        producto_id=producto.id,
                        nombre_producto=producto.nombre,
                        cantidad=cantidad,
                        precio_unitario=precio_unitario,
                    )
                )
        return detalles

    def crear(self, proveedor_id: str, items: list[dict]) -> Compra:
        if not items:
            raise ValidationError("La compra debe tener al menos una línea.")

        detalles = self._aplicar_items(items)
        compra = Compra(id=new_id(), proveedor_id=proveedor_id, detalles=detalles)
        self.compras.add(compra)
        self.session.commit()
        return compra

    def actualizar(
        self, compra_id: str, proveedor_id: str, items: list[dict]
    ) -> Compra:
        if not items:
            raise ValidationError("La compra debe tener al menos una línea.")

        compra = self.obtener(compra_id)
        if compra.anulada:
            raise ValidationError("No se puede editar una compra anulada.")

        # Revertir el efecto de las líneas actuales y aplicar las nuevas.
        self._revertir_stock(compra)
        compra.proveedor_id = proveedor_id
        nuevos = self._aplicar_items(items)

        self.compras.update(compra)
        self.compras.set_detalles(compra.id, nuevos)
        compra.detalles = nuevos
        self.session.commit()
        return compra


    def listar(self, desde=None, hasta=None) -> list[Compra]:
        return self.compras.list(desde, hasta)

    def obtener(self, compra_id: str) -> Compra:
        compra = self.compras.get(compra_id)
        if compra is None:
            raise NotFoundError("Compra no encontrada.")
        return compra

    def _revertir_stock(self, compra: Compra) -> None:
        for detalle in compra.detalles:
            if detalle.tipo == TipoLineaCompra.INSUMO.value:
                insumo = self.insumos.get(detalle.insumo_id)
                if insumo is None:
                    continue
                if insumo.stock < detalle.cantidad:
                    raise ValidationError(
                        f"Stock insuficiente del insumo '{insumo.nombre}'."
                    )
                insumo.stock -= detalle.cantidad
                valor, cantidad = self.compras.suma_compras_insumo(
                    insumo.id, excluir_compra=compra.id
                )
                insumo.costo_unitario = (valor / cantidad) if cantidad > 0 else 0.0
                self.insumos.update(insumo)
            else:
                producto = self.productos.get(detalle.producto_id)
                if producto is None:
                    continue
                if producto.stock < detalle.cantidad:
                    raise ValidationError(
                        f"Stock insuficiente de '{producto.nombre}'."
                    )
                producto.stock -= int(round(detalle.cantidad))
                valor, cantidad = self.compras.suma_compras_producto(
                    producto.id, excluir_compra=compra.id
                )
                producto.costo = (valor / cantidad) if cantidad > 0 else 0.0
                self.productos.update(producto)

    def anular(self, compra_id: str) -> Compra:
        compra = self.obtener(compra_id)
        compra.anular()
        self._revertir_stock(compra)
        self.compras.update(compra)
        self.session.commit()
        return compra

    def eliminar(self, compra_id: str) -> None:
        compra = self.obtener(compra_id)
        if not compra.anulada:
            self._revertir_stock(compra)
        self.compras.delete(compra.id)
        self.session.commit()
