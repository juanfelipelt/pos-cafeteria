from sqlalchemy.orm import Session

from application.events import event_bus
from application.utils import new_id
from domain.entities.detalle_venta import DetalleVenta
from domain.entities.pago import Pago
from domain.entities.venta import Venta
from domain.exceptions import NotFoundError, ValidationError
from domain.repositories.producto_repository import ProductoRepository
from domain.repositories.venta_repository import VentaRepository


class VentaService:
    def __init__(
        self,
        ventas: VentaRepository,
        productos: ProductoRepository,
        session: Session,
    ) -> None:
        self.ventas = ventas
        self.productos = productos
        self.session = session

    def crear(
        self,
        items: list[dict],
        pagos: list[dict],
        usuario_id: str | None = None,
    ) -> Venta:
        if not items:
            raise ValidationError("La venta debe tener al menos un producto.")

        detalles: list[DetalleVenta] = []
        for item in items:
            producto = self.productos.get(item["producto_id"])
            if producto is None:
                raise NotFoundError(f"Producto no encontrado: {item['producto_id']}")
            if not producto.estado:
                raise ValidationError(f"Producto inactivo: {producto.nombre}")

            cantidad = item["cantidad"]
            if cantidad > producto.stock:
                raise ValidationError(
                    f"Stock insuficiente para '{producto.nombre}' "
                    f"(disponible: {producto.stock})."
                )

            detalles.append(
                DetalleVenta(
                    id=new_id(),
                    producto_id=producto.id,
                    nombre_producto=producto.nombre,
                    cantidad=cantidad,
                    precio_unitario=producto.precio,
                )
            )
            producto.stock -= cantidad
            self.productos.update(producto)

        venta = Venta(id=new_id(), usuario_id=usuario_id, detalles=detalles)
        for pago in pagos:
            venta.registrar_pago(
                Pago(
                    id=new_id(),
                    monto=pago["monto"],
                    metodo=pago["metodo"],
                    referencia=pago.get("referencia"),
                )
            )

        self.ventas.add(venta)
        self.session.commit()
        event_bus.publish("venta_creada", venta.to_dict())
        return venta

    def listar(self, desde=None, hasta=None) -> list[Venta]:
        return self.ventas.list(desde, hasta)

    def obtener(self, venta_id: str) -> Venta:
        venta = self.ventas.get(venta_id)
        if venta is None:
            raise NotFoundError("Venta no encontrada.")
        return venta

    def registrar_pago(
        self, venta_id: str, monto: float, metodo: str, referencia: str | None = None
    ) -> Venta:
        venta = self.obtener(venta_id)
        venta.registrar_pago(
            Pago(id=new_id(), monto=monto, metodo=metodo, referencia=referencia)
        )
        self.ventas.update(venta)
        self.session.commit()
        return venta

    def anular(self, venta_id: str) -> Venta:
        venta = self.obtener(venta_id)
        venta.anular()

        for detalle in venta.detalles:
            producto = self.productos.get(detalle.producto_id)
            if producto is not None:
                producto.stock += detalle.cantidad
                self.productos.update(producto)

        self.ventas.update(venta)
        self.session.commit()
        event_bus.publish("venta_anulada", venta.to_dict())
        return venta

    def eliminar(self, venta_id: str) -> None:
        venta = self.obtener(venta_id)

        if not venta.anulada:
            for detalle in venta.detalles:
                producto = self.productos.get(detalle.producto_id)
                if producto is not None:
                    producto.stock += detalle.cantidad
                    self.productos.update(producto)

        self.ventas.delete(venta.id)
        self.session.commit()
        event_bus.publish("venta_eliminada", venta.to_dict())
