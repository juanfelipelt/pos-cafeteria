from sqlalchemy.orm import Session

from application.costos import costos_productos
from application.events import event_bus
from application.utils import new_id
from domain.entities.detalle_receta import DetalleReceta
from domain.entities.detalle_venta import DetalleVenta
from domain.entities.enums import TipoComponente
from domain.entities.pago import Pago
from domain.entities.venta import Venta
from domain.exceptions import NotFoundError, ValidationError
from domain.repositories.insumo_repository import InsumoRepository
from domain.repositories.producto_repository import ProductoRepository
from domain.repositories.receta_repository import RecetaRepository
from domain.repositories.venta_repository import VentaRepository


class VentaService:
    def __init__(
        self,
        ventas: VentaRepository,
        productos: ProductoRepository,
        insumos: InsumoRepository,
        recetas: RecetaRepository,
        session: Session,
    ) -> None:
        self.ventas = ventas
        self.productos = productos
        self.insumos = insumos
        self.recetas = recetas
        self.session = session

    def _recetas_por_producto(self) -> dict[str, list[DetalleReceta]]:
        mapa: dict[str, list[DetalleReceta]] = {}
        for detalle in self.recetas.list_all():
            mapa.setdefault(detalle.producto_id, []).append(detalle)
        return mapa

    def _ajustar_componentes(
        self,
        producto_id: str,
        cantidad: float,
        recetas: dict[str, list[DetalleReceta]],
        signo: int,
        visitados: frozenset[str],
    ) -> None:
        """Consume (signo=-1) o reintegra (signo=+1) los componentes y sus
        dependencias recursivamente."""
        if producto_id in visitados:
            return
        visitados = visitados | {producto_id}

        for detalle in recetas.get(producto_id, []):
            if (
                detalle.tipo == TipoComponente.PRODUCTO.value
                and detalle.componente_producto_id
            ):
                comp = self.productos.get(detalle.componente_producto_id)
                if comp is None:
                    continue
                comp_qty = detalle.cantidad * cantidad
                comp.stock = max(0, comp.stock + signo * int(round(comp_qty)))
                self.productos.update(comp)
                self._ajustar_componentes(
                    comp.id, comp_qty, recetas, signo, visitados
                )
            else:
                insumo = self.insumos.get(detalle.insumo_id)
                if insumo is None:
                    continue
                insumo.stock = max(
                    0.0, insumo.stock + signo * detalle.cantidad * cantidad
                )
                self.insumos.update(insumo)

    def crear(
        self,
        items: list[dict],
        pagos: list[dict],
        usuario_id: str | None = None,
    ) -> Venta:
        if not items:
            raise ValidationError("La venta debe tener al menos un producto.")

        costos_insumos = {i.id: i.costo_unitario for i in self.insumos.list()}
        recetas = self._recetas_por_producto()
        costos = costos_productos(
            self.productos.list(), self.recetas.list_all(), costos_insumos
        )

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
                    costo_unitario=costos.get(producto.id, 0.0),
                )
            )
            producto.stock -= cantidad
            self.productos.update(producto)

            # Consumo de insumos y de productos componentes (combos).
            self._ajustar_componentes(
                producto.id, float(cantidad), recetas, -1, frozenset()
            )

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

    def _reintegrar_stock(self, venta: Venta) -> None:
        recetas = self._recetas_por_producto()
        for detalle in venta.detalles:
            producto = self.productos.get(detalle.producto_id)
            if producto is None:
                continue
            producto.stock += detalle.cantidad
            self.productos.update(producto)
            self._ajustar_componentes(
                producto.id, float(detalle.cantidad), recetas, 1, frozenset()
            )

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
        self._reintegrar_stock(venta)
        self.ventas.update(venta)
        self.session.commit()
        event_bus.publish("venta_anulada", venta.to_dict())
        return venta

    def eliminar(self, venta_id: str) -> None:
        venta = self.obtener(venta_id)

        if not venta.anulada:
            self._reintegrar_stock(venta)

        self.ventas.delete(venta.id)
        self.session.commit()
        event_bus.publish("venta_eliminada", venta.to_dict())
