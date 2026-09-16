from sqlalchemy.orm import Session

from application.costos import costos_productos
from application.utils import new_id
from domain.entities.detalle_receta import DetalleReceta
from domain.entities.enums import TipoComponente
from domain.exceptions import NotFoundError, ValidationError
from domain.repositories.insumo_repository import InsumoRepository
from domain.repositories.producto_repository import ProductoRepository
from domain.repositories.receta_repository import RecetaRepository


class RecetaService:
    def __init__(
        self,
        recetas: RecetaRepository,
        productos: ProductoRepository,
        insumos: InsumoRepository,
        session: Session,
    ) -> None:
        self.recetas = recetas
        self.productos = productos
        self.insumos = insumos
        self.session = session

    def obtener(self, producto_id: str) -> list[dict]:
        producto = self.productos.get(producto_id)
        if producto is None:
            raise NotFoundError("Producto no encontrado.")

        costos_insumos = {i.id: i.costo_unitario for i in self.insumos.list()}
        costos = costos_productos(
            self.productos.list(), self.recetas.list_all(), costos_insumos
        )

        items = []
        for detalle in self.recetas.list_by_producto(producto_id):
            if detalle.tipo == TipoComponente.PRODUCTO.value:
                comp = self.productos.get(detalle.componente_producto_id)
                costo_unitario = costos.get(detalle.componente_producto_id, 0.0)
                items.append(
                    {
                        "id": detalle.id,
                        "tipo": detalle.tipo,
                        "componente_id": detalle.componente_producto_id,
                        "nombre": comp.nombre if comp else "(producto eliminado)",
                        "unidad": comp.tipo if comp else "",
                        "costo_unitario": costo_unitario,
                        "cantidad": detalle.cantidad,
                        "subtotal": costo_unitario * detalle.cantidad,
                    }
                )
            else:
                insumo = self.insumos.get(detalle.insumo_id)
                costo_unitario = insumo.costo_unitario if insumo else 0.0
                items.append(
                    {
                        "id": detalle.id,
                        "tipo": detalle.tipo,
                        "componente_id": detalle.insumo_id,
                        "nombre": insumo.nombre if insumo else "(insumo eliminado)",
                        "unidad": insumo.unidad if insumo else "",
                        "costo_unitario": costo_unitario,
                        "cantidad": detalle.cantidad,
                        "subtotal": costo_unitario * detalle.cantidad,
                    }
                )
        return items

    def _hay_ciclo(
        self, producto_id: str, componentes_producto: set[str]
    ) -> bool:
        grafo: dict[str, set[str]] = {}
        for detalle in self.recetas.list_all():
            if (
                detalle.tipo == TipoComponente.PRODUCTO.value
                and detalle.componente_producto_id
            ):
                grafo.setdefault(detalle.producto_id, set()).add(
                    detalle.componente_producto_id
                )
        grafo[producto_id] = set(componentes_producto)

        pila = [producto_id]
        visto: set[str] = set()
        while pila:
            actual = pila.pop()
            for comp in grafo.get(actual, ()):
                if comp == producto_id:
                    return True
                if comp not in visto:
                    visto.add(comp)
                    pila.append(comp)
        return False

    def establecer(self, producto_id: str, items: list[dict]) -> list[dict]:
        producto = self.productos.get(producto_id)
        if producto is None:
            raise NotFoundError("Producto no encontrado.")
        if producto.tipo not in ("preparado", "compuesto"):
            raise ValidationError(
                "Solo los productos 'preparado' o 'compuesto' tienen componentes."
            )

        detalles: list[DetalleReceta] = []
        componentes_producto: set[str] = set()
        vistos: set[tuple] = set()

        for item in items:
            tipo = item.get("tipo", TipoComponente.INSUMO.value)
            cantidad = item["cantidad"]

            if tipo == TipoComponente.PRODUCTO.value:
                if producto.tipo != "compuesto":
                    raise ValidationError(
                        "Un producto 'preparado' solo admite insumos en su receta."
                    )
                comp_id = item.get("componente_producto_id")
                if self.productos.get(comp_id) is None:
                    raise NotFoundError(f"Producto componente no encontrado: {comp_id}")
                if comp_id == producto_id:
                    raise ValidationError("Un producto no puede componerse de sí mismo.")
                clave = (tipo, comp_id)
                if clave in vistos:
                    raise ValidationError("Hay componentes repetidos en la receta.")
                vistos.add(clave)
                componentes_producto.add(comp_id)
                detalles.append(
                    DetalleReceta(
                        id=new_id(),
                        producto_id=producto_id,
                        tipo=tipo,
                        componente_producto_id=comp_id,
                        cantidad=cantidad,
                    )
                )
            else:
                insumo_id = item.get("insumo_id")
                if self.insumos.get(insumo_id) is None:
                    raise NotFoundError(f"Insumo no encontrado: {insumo_id}")
                clave = (tipo, insumo_id)
                if clave in vistos:
                    raise ValidationError("Hay componentes repetidos en la receta.")
                vistos.add(clave)
                detalles.append(
                    DetalleReceta(
                        id=new_id(),
                        producto_id=producto_id,
                        tipo=tipo,
                        insumo_id=insumo_id,
                        cantidad=cantidad,
                    )
                )

        if componentes_producto and self._hay_ciclo(producto_id, componentes_producto):
            raise ValidationError(
                "La receta genera un ciclo (un producto se compone, directa o "
                "indirectamente, de sí mismo)."
            )

        self.recetas.set_for_producto(producto_id, detalles)
        self.session.commit()
        return self.obtener(producto_id)
