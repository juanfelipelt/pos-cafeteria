"""Servicio de ventas (caso de uso: "Registrar y anular ventas").

¿Qué resuelve?
- Registrar una venta con sus productos, descontando stock.
- Descontar también los insumos y productos componentes según las recetas
  (una venta de un producto preparado consume sus insumos; un combo consume
  sus componentes de forma recursiva).
- Registrar pagos, anular ventas y eliminarlas reintegrando el stock.
- Publicar eventos para la interfaz en tiempo real.

¿Cómo usa los repositorios?
- ``VentaRepository``: guarda y consulta ventas.
- ``ProductoRepository``, ``InsumoRepository`` y ``RecetaRepository``:
  validan stock y permiten ajustar componentes.
- ``Session``: confirma los cambios.
- ``event_bus``: notifica venta_creada, venta_anulada y venta_eliminada.

Al crear la venta se "congela" el costo unitario de cada producto (campo
``costo_unitario`` del detalle) para que los reportes históricos no cambien
aunque después se modifiquen los costos.
"""

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
    """Registra ventas y mantiene el inventario en sincronía."""

    def __init__(
        self,
        ventas: VentaRepository,
        productos: ProductoRepository,
        insumos: InsumoRepository,
        recetas: RecetaRepository,
        session: Session,
    ) -> None:
        """Guarda las dependencias del servicio.

        Parámetros:
            ventas: repositorio de ventas.
            productos: repositorio de productos.
            insumos: repositorio de insumos.
            recetas: repositorio de recetas.
            session: sesión de SQLAlchemy para confirmar cambios.
        """
        self.ventas = ventas
        self.productos = productos
        self.insumos = insumos
        self.recetas = recetas
        self.session = session

    def _recetas_por_producto(self) -> dict[str, list[DetalleReceta]]:
        """Agrupa todos los detalles de receta por producto.

        Retorna:
            Diccionario producto_id -> lista de componentes de su receta.
        """
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
        dependencias recursivamente.

        Parámetros:
            producto_id: producto cuyos componentes se van a ajustar.
            cantidad: unidades del producto (se multiplican por las cantidades
                de la receta).
            recetas: mapa producto_id -> componentes.
            signo: -1 para descontar (venta), +1 para devolver (anulación).
            visitados: conjunto de productos ya procesados, para evitar ciclos.

        Nota:
            El stock nunca queda negativo: se usa ``max(0, ...)``.
        """
        # Guarda contra ciclos: si ya se procesó este producto, se corta.
        if producto_id in visitados:
            return
        visitados = visitados | {producto_id}

        for detalle in recetas.get(producto_id, []):
            if (
                detalle.tipo == TipoComponente.PRODUCTO.value
                and detalle.componente_producto_id
            ):
                # --- El componente es otro producto (combo/anidado) ---
                comp = self.productos.get(detalle.componente_producto_id)
                if comp is None:
                    continue
                # Cantidad total del componente = cantidad de receta * vendidos.
                comp_qty = detalle.cantidad * cantidad
                comp.stock = max(0, comp.stock + signo * int(round(comp_qty)))
                self.productos.update(comp)
                # Se desciende recursivamente a los componentes del componente.
                self._ajustar_componentes(
                    comp.id, comp_qty, recetas, signo, visitados
                )
            else:
                # --- El componente es un insumo ---
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
        """Registra una venta y descuenta el inventario.

        Parámetros:
            items: líneas de la venta; cada una con ``producto_id`` y
                ``cantidad``.
            pagos: pagos asociados; cada uno con ``monto``, ``metodo`` y
                ``referencia`` opcional.
            usuario_id: id del usuario que registra la venta (opcional).

        Retorna:
            La venta creada y confirmada.

        Lanza:
            ValidationError: si no hay items, el producto está inactivo o no
                hay stock suficiente.
            NotFoundError: si algún producto no existe.
        """
        # Una venta vacía no tiene sentido.
        if not items:
            raise ValidationError("La venta debe tener al menos un producto.")

        # Se preparan los mapas de costos y recetas una sola vez (más eficiente).
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
            # No se venden productos desactivados.
            if not producto.estado:
                raise ValidationError(f"Producto inactivo: {producto.nombre}")

            cantidad = item["cantidad"]
            # Validación de stock disponible antes de vender.
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
                    # Se congela el costo actual para la historia de la venta.
                    costo_unitario=costos.get(producto.id, 0.0),
                )
            )
            # Se descuenta el stock del producto vendido.
            producto.stock -= cantidad
            self.productos.update(producto)

            # Consumo de insumos y de productos componentes (combos).
            self._ajustar_componentes(
                producto.id, float(cantidad), recetas, -1, frozenset()
            )

        venta = Venta(id=new_id(), usuario_id=usuario_id, detalles=detalles)
        # Se registran los pagos recibidos (puede haber varios métodos).
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
        """Lista las ventas, con filtro opcional por rango de fechas.

        Parámetros:
            desde: fecha/hora inicial (opcional).
            hasta: fecha/hora final (opcional).

        Retorna:
            Lista de ventas.
        """
        return self.ventas.list(desde, hasta)

    def obtener(self, venta_id: str) -> Venta:
        """Busca una venta por id.

        Parámetros:
            venta_id: identificador de la venta.

        Retorna:
            La venta encontrada.

        Lanza:
            NotFoundError: si no existe.
        """
        venta = self.ventas.get(venta_id)
        if venta is None:
            raise NotFoundError("Venta no encontrada.")
        return venta

    def _reintegrar_stock(self, venta: Venta) -> None:
        """Devuelve al inventario el stock de una venta (al anular/eliminar).

        Reintegra los productos vendidos y, recursivamente, sus componentes
        (insumos y productos de combos) con signo +1.

        Parámetros:
            venta: venta cuyo stock se quiere reintegrar.
        """
        recetas = self._recetas_por_producto()
        for detalle in venta.detalles:
            producto = self.productos.get(detalle.producto_id)
            if producto is None:
                continue
            # Se devuelve la cantidad vendida del producto.
            producto.stock += detalle.cantidad
            self.productos.update(producto)
            # Y se devuelven sus componentes (signo +1).
            self._ajustar_componentes(
                producto.id, float(detalle.cantidad), recetas, 1, frozenset()
            )

    def registrar_pago(
        self, venta_id: str, monto: float, metodo: str, referencia: str | None = None
    ) -> Venta:
        """Agrega un pago a una venta existente.

        Parámetros:
            venta_id: id de la venta.
            monto: valor pagado.
            metodo: método de pago (efectivo, tarjeta, transferencia).
            referencia: referencia del pago (opcional).

        Retorna:
            La venta con el pago agregado.

        Lanza:
            NotFoundError: si la venta no existe.
        """
        venta = self.obtener(venta_id)
        venta.registrar_pago(
            Pago(id=new_id(), monto=monto, metodo=metodo, referencia=referencia)
        )
        self.ventas.update(venta)
        self.session.commit()
        return venta

    def anular(self, venta_id: str) -> Venta:
        """Anula una venta y devuelve el stock al inventario.

        Parámetros:
            venta_id: id de la venta a anular.

        Retorna:
            La venta anulada.

        Lanza:
            NotFoundError: si no existe.
        """
        venta = self.obtener(venta_id)
        venta.anular()
        # Al anular, los productos y componentes vuelven al inventario.
        self._reintegrar_stock(venta)
        self.ventas.update(venta)
        self.session.commit()
        event_bus.publish("venta_anulada", venta.to_dict())
        return venta

    def eliminar(self, venta_id: str) -> None:
        """Elimina una venta, reintegrando el stock si no estaba anulada.

        Parámetros:
            venta_id: id de la venta a eliminar.

        Lanza:
            NotFoundError: si no existe.
        """
        venta = self.obtener(venta_id)

        # Si la venta no estaba anulada, su stock aún está descontado:
        # hay que devolverlo antes de borrarla. Si ya estaba anulada, el stock
        # ya fue reintegrado y no se debe tocar de nuevo.
        if not venta.anulada:
            self._reintegrar_stock(venta)

        self.ventas.delete(venta.id)
        self.session.commit()
        event_bus.publish("venta_eliminada", venta.to_dict())
