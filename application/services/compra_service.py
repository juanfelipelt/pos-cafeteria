"""Servicio de compras a proveedores (caso de uso: "Compras / Entradas").

¿Qué resuelve?
- Registrar las compras que se hacen a un proveedor, distinguiendo cada línea
  como insumo o como producto.
- Al comprar, subir el stock y recalcular el costo promedio ponderado.
- Permitir editar, anular y eliminar compras revirtiendo correctamente el
  efecto que tuvieron sobre el inventario.

¿Cómo usa los repositorios?
- ``CompraRepository``: guarda/consulta compras y calcula sumas históricas
  de compras por insumo/producto.
- ``ProductoRepository`` y ``InsumoRepository``: leen y actualizan el stock
  y el costo de los artículos afectados.
- ``Session``: confirma (commit) los cambios al final de cada operación.

Esta es una pieza clave del costeo: los precios de compra determinan el costo
con el que luego se calculan los márgenes y utilidades.
"""

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
    """Costo promedio ponderado.

    Si el inventario actual no tiene costo (stock manual con costo 0) o no hay
    stock, no se diluye: el costo pasa a ser el precio de esta compra.

    Parámetros:
        stock_actual: unidades que ya había en inventario.
        costo_actual: costo unitario que tenían esas unidades.
        cantidad: unidades que se están comprando ahora.
        precio: precio unitario de esta compra.

    Retorna:
        El nuevo costo unitario promedio.
    """
    # Si no hay stock o el costo es 0 (carga manual), se adopta el precio
    # de esta compra tal cual: evita "diluir" el costo con valores falsos.
    if stock_actual <= 0 or costo_actual <= 0:
        return precio
    # Total de unidades tras la compra (cantidad vieja + nueva).
    total = stock_actual + cantidad
    # Caso borde: cantidades negativas/ajustes dejarían un total inválido.
    if total <= 0:
        return precio
    # Fórmula clásica: valor viejo + valor nuevo, dividido por el total.
    return (stock_actual * costo_actual + cantidad * precio) / total


class CompraService:
    """Registra y administra las compras hechas a proveedores."""

    def __init__(
        self,
        compras: CompraRepository,
        productos: ProductoRepository,
        insumos: InsumoRepository,
        session: Session,
    ) -> None:
        """Guarda las dependencias del servicio.

        Parámetros:
            compras: repositorio de compras.
            productos: repositorio de productos.
            insumos: repositorio de insumos.
            session: sesión de SQLAlchemy para confirmar cambios.
        """
        self.compras = compras
        self.productos = productos
        self.insumos = insumos
        self.session = session

    def _aplicar_items(self, items: list[dict]) -> list[DetalleCompra]:
        """Aplica cada línea (sube stock y recalcula costo) y devuelve los
        detalles de dominio.

        Parámetros:
            items: lista de diccionarios, cada uno con ``tipo``, ``cantidad``,
                ``precio_unitario`` y el id del insumo o producto según el tipo.

        Retorna:
            La lista de ``DetalleCompra`` construidos.

        Lanza:
            NotFoundError: si el insumo o producto de una línea no existe.
        """
        detalles: list[DetalleCompra] = []
        for item in items:
            # Por defecto una línea es de producto si no se especifica el tipo.
            tipo = item.get("tipo", TipoLineaCompra.PRODUCTO.value)
            cantidad = item["cantidad"]
            precio_unitario = item["precio_unitario"]

            if tipo == TipoLineaCompra.INSUMO.value:
                # --- Línea de INSUMO ---
                insumo = self.insumos.get(item["insumo_id"])
                if insumo is None:
                    raise NotFoundError(f"Insumo no encontrado: {item['insumo_id']}")
                # Se recalcula el costo unitario con promedio ponderado antes
                # de subir el stock (usa el stock y costo anteriores).
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
                # --- Línea de PRODUCTO ---
                producto = self.productos.get(item["producto_id"])
                if producto is None:
                    raise NotFoundError(
                        f"Producto no encontrado: {item['producto_id']}"
                    )
                # Misma lógica de promedio ponderado para el costo del producto.
                producto.costo = _promedio_ponderado(
                    producto.stock, producto.costo, cantidad, precio_unitario
                )
                # El stock de productos es entero: se redondea la cantidad.
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
        """Registra una compra nueva con sus líneas.

        Parámetros:
            proveedor_id: id del proveedor al que se le compró.
            items: líneas de la compra (insumos y/o productos).

        Retorna:
            La compra creada y confirmada.

        Lanza:
            ValidationError: si no hay ninguna línea.
        """
        # Una compra sin líneas no tiene sentido: se rechaza.
        if not items:
            raise ValidationError("La compra debe tener al menos una línea.")

        # Se aplican las líneas: sube stock y recalcula costos.
        detalles = self._aplicar_items(items)
        compra = Compra(id=new_id(), proveedor_id=proveedor_id, detalles=detalles)
        self.compras.add(compra)
        self.session.commit()
        return compra

    def actualizar(
        self, compra_id: str, proveedor_id: str, items: list[dict]
    ) -> Compra:
        """Edita una compra existente reemplazando todas sus líneas.

        Estrategia: primero se revierte el efecto de las líneas actuales y
        luego se aplican las nuevas, para que stock y costos queden correctos.

        Parámetros:
            compra_id: id de la compra a editar.
            proveedor_id: nuevo proveedor (o el mismo).
            items: nuevas líneas de la compra.

        Retorna:
            La compra actualizada.

        Lanza:
            ValidationError: si no hay líneas o la compra está anulada.
        """
        # Igual que en crear, debe haber al menos una línea.
        if not items:
            raise ValidationError("La compra debe tener al menos una línea.")

        compra = self.obtener(compra_id)
        # Una compra anulada es histórica: no se puede editar.
        if compra.anulada:
            raise ValidationError("No se puede editar una compra anulada.")

        # Revertir el efecto de las líneas actuales y aplicar las nuevas.
        self._revertir_stock(compra)
        compra.proveedor_id = proveedor_id
        nuevos = self._aplicar_items(items)

        # Se guarda la cabecera, se reemplazan los detalles y se sincroniza
        # el objeto en memoria con los nuevos detalles.
        self.compras.update(compra)
        self.compras.set_detalles(compra.id, nuevos)
        compra.detalles = nuevos
        self.session.commit()
        return compra


    def listar(self, desde=None, hasta=None) -> list[Compra]:
        """Lista las compras, opcionalmente filtradas por rango de fechas.

        Parámetros:
            desde: fecha/hora inicial del filtro (opcional).
            hasta: fecha/hora final del filtro (opcional).

        Retorna:
            Lista de compras que cumplen el rango.
        """
        return self.compras.list(desde, hasta)

    def obtener(self, compra_id: str) -> Compra:
        """Busca una compra por id.

        Parámetros:
            compra_id: identificador de la compra.

        Retorna:
            La compra encontrada.

        Lanza:
            NotFoundError: si la compra no existe.
        """
        compra = self.compras.get(compra_id)
        if compra is None:
            raise NotFoundError("Compra no encontrada.")
        return compra

    def _revertir_stock(self, compra: Compra) -> None:
        """Deshace el efecto en inventario de todas las líneas de una compra.

        Para cada línea resta el stock que había sumado y recalcula el costo
        con el promedio histórico de las compras restantes (excluyendo esta).

        Parámetros:
            compra: compra cuyos efectos se quieren revertir.

        Lanza:
            ValidationError: si no hay stock suficiente para revertir.
        """
        for detalle in compra.detalles:
            if detalle.tipo == TipoLineaCompra.INSUMO.value:
                # --- Revertir un INSUMO ---
                insumo = self.insumos.get(detalle.insumo_id)
                # Si el insumo ya no existe, no hay nada que revertir.
                if insumo is None:
                    continue
                # No se puede dejar el stock en negativo.
                if insumo.stock < detalle.cantidad:
                    raise ValidationError(
                        f"Stock insuficiente del insumo '{insumo.nombre}'."
                    )
                insumo.stock -= detalle.cantidad
                # Se recalcula el costo con las compras restantes (sin esta).
                valor, cantidad = self.compras.suma_compras_insumo(
                    insumo.id, excluir_compra=compra.id
                )
                insumo.costo_unitario = (valor / cantidad) if cantidad > 0 else 0.0
                self.insumos.update(insumo)
            else:
                # --- Revertir un PRODUCTO ---
                producto = self.productos.get(detalle.producto_id)
                if producto is None:
                    continue
                if producto.stock < detalle.cantidad:
                    raise ValidationError(
                        f"Stock insuficiente de '{producto.nombre}'."
                    )
                # El stock de productos es entero: se redondea la resta.
                producto.stock -= int(round(detalle.cantidad))
                # Recalculo del costo con el resto de compras del producto.
                valor, cantidad = self.compras.suma_compras_producto(
                    producto.id, excluir_compra=compra.id
                )
                producto.costo = (valor / cantidad) if cantidad > 0 else 0.0
                self.productos.update(producto)

    def anular(self, compra_id: str) -> Compra:
        """Marca una compra como anulada y revierte su efecto en inventario.

        Parámetros:
            compra_id: id de la compra a anular.

        Retorna:
            La compra anulada.

        Lanza:
            NotFoundError: si la compra no existe.
        """
        compra = self.obtener(compra_id)
        compra.anular()
        # Se deshacen stock y costos que había provocado la compra.
        self._revertir_stock(compra)
        self.compras.update(compra)
        self.session.commit()
        return compra

    def eliminar(self, compra_id: str) -> None:
        """Elimina una compra, revirtiendo antes su efecto si no estaba anulada.

        Parámetros:
            compra_id: id de la compra a eliminar.

        Lanza:
            NotFoundError: si la compra no existe.
        """
        compra = self.obtener(compra_id)
        # Si aún no estaba anulada, hay que revertir su efecto en inventario;
        # si ya estaba anulada, ese efecto ya fue revertido antes.
        if not compra.anulada:
            self._revertir_stock(compra)
        self.compras.delete(compra.id)
        self.session.commit()
