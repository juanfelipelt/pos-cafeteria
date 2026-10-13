"""Servicio de recetas (caso de uso: "Composición de productos").

¿Qué resuelve?
- Definir de qué está hecho un producto "preparado" o "compuesto":
  insumos y/o otros productos, con sus cantidades.
- Mostrar la receta con el costo unitario y subtotal de cada componente.
- Validar que no haya productos repetidos, que un "preparado" solo use
  insumos y que no se generen ciclos (un producto que se contenga a sí mismo).

¿Cómo usa los repositorios?
- ``RecetaRepository``: guarda los detalles de la receta por producto.
- ``ProductoRepository`` e ``InsumoRepository``: validan que los componentes
  existan y aportan nombres y costos.
- ``Session``: confirma los cambios.

La receta es la base para que el costeo calcule el costo de productos
preparados y compuestos.
"""

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
    """Gestiona las recetas (componentes) de los productos."""

    def __init__(
        self,
        recetas: RecetaRepository,
        productos: ProductoRepository,
        insumos: InsumoRepository,
        session: Session,
    ) -> None:
        """Guarda las dependencias del servicio.

        Parámetros:
            recetas: repositorio de recetas.
            productos: repositorio de productos.
            insumos: repositorio de insumos.
            session: sesión de SQLAlchemy para confirmar cambios.
        """
        self.recetas = recetas
        self.productos = productos
        self.insumos = insumos
        self.session = session

    def obtener(self, producto_id: str) -> list[dict]:
        """Devuelve la receta de un producto con costos y subtotales.

        Parámetros:
            producto_id: id del producto cuya receta se quiere.

        Retorna:
            Lista de componentes; cada uno indica tipo, nombre, unidad,
            costo unitario, cantidad y subtotal.

        Lanza:
            NotFoundError: si el producto no existe.
        """
        producto = self.productos.get(producto_id)
        if producto is None:
            raise NotFoundError("Producto no encontrado.")

        # Costos de insumos y costos calculados de los productos (para combos).
        costos_insumos = {i.id: i.costo_unitario for i in self.insumos.list()}
        costos = costos_productos(
            self.productos.list(), self.recetas.list_all(), costos_insumos
        )

        items = []
        for detalle in self.recetas.list_by_producto(producto_id):
            if detalle.tipo == TipoComponente.PRODUCTO.value:
                # --- Componente que es otro PRODUCTO ---
                comp = self.productos.get(detalle.componente_producto_id)
                costo_unitario = costos.get(detalle.componente_producto_id, 0.0)
                items.append(
                    {
                        "id": detalle.id,
                        "tipo": detalle.tipo,
                        "componente_id": detalle.componente_producto_id,
                        # Si el producto fue eliminado, se muestra un aviso.
                        "nombre": comp.nombre if comp else "(producto eliminado)",
                        "unidad": comp.tipo if comp else "",
                        "costo_unitario": costo_unitario,
                        "cantidad": detalle.cantidad,
                        "subtotal": costo_unitario * detalle.cantidad,
                    }
                )
            else:
                # --- Componente que es un INSUMO ---
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
        """Detecta si la receta propuesta genera un ciclo.

        Se construye un grafo producto -> productos componentes y se recorre
        desde el producto editado; si se vuelve a encontrar el mismo producto,
        hay un ciclo (por ejemplo A contiene B y B contiene A).

        Parámetros:
            producto_id: producto que se está editando.
            componentes_producto: productos que formarán su receta.

        Retorna:
            ``True`` si hay ciclo, ``False`` si no.
        """
        # Grafo de dependencias entre productos, según las recetas actuales.
        grafo: dict[str, set[str]] = {}
        for detalle in self.recetas.list_all():
            if (
                detalle.tipo == TipoComponente.PRODUCTO.value
                and detalle.componente_producto_id
            ):
                grafo.setdefault(detalle.producto_id, set()).add(
                    detalle.componente_producto_id
                )
        # Se añade la relación propuesta (aún no guardada) para evaluarla.
        grafo[producto_id] = set(componentes_producto)

        # Recorrido iterativo (DFS con pila) buscando llegar de nuevo al origen.
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
        """Reemplaza por completo la receta de un producto.

        Valida tipo de producto, existencia de componentes, repetidos y ciclos,
        y luego guarda la nueva receta. Al final devuelve la receta con costos.

        Parámetros:
            producto_id: id del producto a configurar.
            items: lista de componentes; cada uno con ``tipo``, ``cantidad`` y
                el id del insumo o producto componente.

        Retorna:
            La receta del producto ya guardada (con costos).

        Lanza:
            NotFoundError: si el producto o algún componente no existe.
            ValidationError: si las reglas de negocio no se cumplen.
        """
        producto = self.productos.get(producto_id)
        if producto is None:
            raise NotFoundError("Producto no encontrado.")
        # Solo los productos preparados o compuestos pueden tener receta.
        if producto.tipo not in ("preparado", "compuesto"):
            raise ValidationError(
                "Solo los productos 'preparado' o 'compuesto' tienen componentes."
            )

        detalles: list[DetalleReceta] = []
        componentes_producto: set[str] = set()
        # Control de componentes repetidos: la clave es (tipo, id del componente).
        vistos: set[tuple] = set()

        for item in items:
            # Por defecto se asume que el componente es un insumo.
            tipo = item.get("tipo", TipoComponente.INSUMO.value)
            cantidad = item["cantidad"]

            if tipo == TipoComponente.PRODUCTO.value:
                # --- Componente de tipo PRODUCTO ---
                # Un "preparado" es de insumos; solo un "compuesto" admite
                # otros productos como componentes.
                if producto.tipo != "compuesto":
                    raise ValidationError(
                        "Un producto 'preparado' solo admite insumos en su receta."
                    )
                comp_id = item.get("componente_producto_id")
                # El producto componente debe existir.
                if self.productos.get(comp_id) is None:
                    raise NotFoundError(f"Producto componente no encontrado: {comp_id}")
                # Un producto no puede ser componente de sí mismo (ciclo directo).
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
                # --- Componente de tipo INSUMO ---
                insumo_id = item.get("insumo_id")
                # El insumo debe existir.
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

        # Validación global: no se permiten ciclos indirectos entre productos.
        if componentes_producto and self._hay_ciclo(producto_id, componentes_producto):
            raise ValidationError(
                "La receta genera un ciclo (un producto se compone, directa o "
                "indirectamente, de sí mismo)."
            )

        # Se reemplaza la receta completa y se devuelve ya calculada.
        self.recetas.set_for_producto(producto_id, detalles)
        self.session.commit()
        return self.obtener(producto_id)
