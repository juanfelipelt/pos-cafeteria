"""Repositorios "falsos" (fakes) para las pruebas unitarias.

¿Por qué existen? Los servicios de la aplicación guardan y leen datos a través
de repositorios (patrón Repository). En las pruebas unitarias no queremos
depender de una base de datos real (sería lento y frágil). En su lugar usamos
estos "dobles de prueba" que guardan los objetos en un diccionario en memoria.

Cada Fake...Repository hereda de la interfaz real del dominio y la implementa
de forma sencilla con un diccionario `data` (id -> objeto). Así podemos probar
la lógica de negocio de los servicios de forma rápida y aislada.
"""

from domain.repositories.compra_repository import CompraRepository
from domain.repositories.configuracion_repository import ConfiguracionRepository
from domain.repositories.costo_fijo_repository import CostoFijoRepository
from domain.repositories.insumo_repository import InsumoRepository
from domain.repositories.producto_repository import ProductoRepository
from domain.repositories.receta_repository import RecetaRepository
from domain.repositories.usuario_repository import UsuarioRepository
from domain.repositories.venta_repository import VentaRepository


class FakeSession:
    """Sustituto de una sesión de base de datos (transacciones).

    Los servicios reales reciben una sesión SQLAlchemy y llaman a commit,
    rollback y close. Aquí solo necesitamos que esos métodos existan y no
    fallen: no hay base de datos real que confirmar.
    """

    def commit(self) -> None:
        # No hace nada: en memoria no hay transacción que confirmar.
        pass

    def rollback(self) -> None:
        # No hace nada: no hay transacción que revertir.
        pass

    def close(self) -> None:
        # No hace nada: no hay conexión que cerrar.
        pass


class FakeProductoRepository(ProductoRepository):
    """Repositorio en memoria de productos (misma interfaz que el real).

    `data` es un diccionario {id: Producto} que hace de "tabla" de productos.
    """

    def __init__(self) -> None:
        self.data = {}

    def get(self, id: str):
        # Devuelve el producto con ese id, o None si no existe.
        return self.data.get(id)

    def list(self, filtro=None, categoria_id=None, solo_activos=False):
        # Devuelve todos los productos guardados (el fake ignora los filtros).
        return list(self.data.values())

    def add(self, producto):
        # Guarda (o reemplaza) el producto usando su id como clave.
        self.data[producto.id] = producto
        return producto

    def update(self, producto):
        # Como ya usamos el id como clave, actualizar es volver a guardar.
        self.data[producto.id] = producto
        return producto


class FakeVentaRepository(VentaRepository):
    """Repositorio en memoria de ventas."""

    def __init__(self) -> None:
        self.data = {}

    def get(self, id: str):
        # Busca una venta por id (None si no existe).
        return self.data.get(id)

    def list(self, desde=None, hasta=None):
        # Lista todas las ventas (el fake ignora el rango de fechas).
        return list(self.data.values())

    def add(self, venta):
        # Guarda (o reemplaza) la venta usando su id como clave.
        self.data[venta.id] = venta
        return venta

    def update(self, venta):
        # Actualizar es volver a guardar con la misma clave.
        self.data[venta.id] = venta
        return venta

    def delete(self, id: str):
        # Elimina la venta si existe; pop con None evita error si no está.
        self.data.pop(id, None)


class FakeCompraRepository(CompraRepository):
    """Repositorio en memoria de compras, con soporte para sus detalles.

    Además de guardar compras, calcula sumas de cantidades y valores por insumo
    o producto, imitando las consultas que haría la base de datos real.
    """

    def __init__(self) -> None:
        self.data = {}

    def get(self, id: str):
        # Busca una compra por id (None si no existe).
        return self.data.get(id)

    def list(self, desde=None, hasta=None):
        # Lista todas las compras (el fake ignora el rango de fechas).
        return list(self.data.values())

    def add(self, compra):
        self.data[compra.id] = compra
        return compra

    def update(self, compra):
        self.data[compra.id] = compra
        return compra

    def set_detalles(self, compra_id, detalles):
        # Reemplaza los detalles (líneas) de una compra concreta.
        compra = self.data.get(compra_id)
        if compra is not None:
            compra.detalles = detalles

    def has_for_proveedor(self, proveedor_id: str):
        # True si alguna compra pertenece a ese proveedor (para impedir borrarlo).
        return any(c.proveedor_id == proveedor_id for c in self.data.values())

    def _suma(self, tipo, attr, valor, excluir_compra):
        # Método auxiliar: recorre los detalles de las compras NO anuladas y suma
        # el valor total (cantidad * precio) y las cantidades de un insumo o
        # producto concreto. `excluir_compra` permite ignorar una compra (por
        # ejemplo, la que se está editando) para recalcular costos.
        total_valor = 0.0
        total_cantidad = 0.0
        for compra in self.data.values():
            # Ignoramos las compras anuladas o la compra que se quiere excluir.
            if compra.anulada or compra.id == excluir_compra:
                continue
            for detalle in compra.detalles:
                # Solo contamos detalles del tipo y con el id que buscamos.
                if detalle.tipo == tipo and getattr(detalle, attr) == valor:
                    total_valor += detalle.cantidad * detalle.precio_unitario
                    total_cantidad += detalle.cantidad
        return total_valor, total_cantidad

    def suma_compras_insumo(self, insumo_id, excluir_compra=None):
        # Sumas totales (valor y cantidad) para un insumo concreto.
        return self._suma("insumo", "insumo_id", insumo_id, excluir_compra)

    def suma_compras_producto(self, producto_id, excluir_compra=None):
        # Sumas totales (valor y cantidad) para un producto concreto.
        return self._suma("producto", "producto_id", producto_id, excluir_compra)

    def delete(self, id: str):
        self.data.pop(id, None)


class FakeUsuarioRepository(UsuarioRepository):
    """Repositorio en memoria de usuarios (incluye búsqueda por email)."""

    def __init__(self) -> None:
        self.data = {}

    def get(self, id: str):
        return self.data.get(id)

    def get_by_email(self, email: str):
        # Recorre los usuarios y devuelve el que tenga ese email (o None).
        for u in self.data.values():
            if u.email == email:
                return u
        return None

    def list(self):
        return list(self.data.values())

    def add(self, usuario):
        self.data[usuario.id] = usuario
        return usuario

    def update(self, usuario):
        self.data[usuario.id] = usuario
        return usuario


class FakeInsumoRepository(InsumoRepository):
    """Repositorio en memoria de insumos (materias primas)."""

    def __init__(self) -> None:
        self.data = {}

    def get(self, id: str):
        return self.data.get(id)

    def list(self, filtro=None, solo_activos=False):
        # Lista todos los insumos (el fake ignora los filtros).
        return list(self.data.values())

    def add(self, insumo):
        self.data[insumo.id] = insumo
        return insumo

    def update(self, insumo):
        self.data[insumo.id] = insumo
        return insumo

    def delete(self, id: str):
        self.data.pop(id, None)


class FakeRecetaRepository(RecetaRepository):
    """Repositorio en memoria de recetas (qué usa cada producto).

    Una "receta" es una lista de detalles; aquí se guardan todos los detalles en
    un solo diccionario y se filtran por producto_id cuando hace falta.
    """

    def __init__(self) -> None:
        self.data = {}

    def list_by_producto(self, producto_id: str):
        # Devuelve solo los detalles de receta que pertenecen a ese producto.
        return [d for d in self.data.values() if d.producto_id == producto_id]

    def list_all(self):
        return list(self.data.values())

    def set_for_producto(self, producto_id, detalles):
        # Reemplaza por completo la receta de un producto: primero borra los
        # detalles actuales y luego guarda los nuevos.
        for key in [k for k, d in self.data.items() if d.producto_id == producto_id]:
            self.data.pop(key)
        for detalle in detalles:
            self.data[detalle.id] = detalle
        return self.list_by_producto(producto_id)

    def delete_by_producto(self, producto_id: str) -> None:
        # Borra todos los detalles de receta del producto indicado.
        for key in [k for k, d in self.data.items() if d.producto_id == producto_id]:
            self.data.pop(key)

    def has_for_insumo(self, insumo_id: str) -> bool:
        # True si algún detalle de receta usa ese insumo (para no borrarlo).
        return any(d.insumo_id == insumo_id for d in self.data.values())


class FakeCostoFijoRepository(CostoFijoRepository):
    """Repositorio en memoria de costos fijos (arriendo, servicios, etc.)."""

    def __init__(self) -> None:
        self.data = {}

    def get(self, id: str):
        return self.data.get(id)

    def list(self, solo_activos: bool = False):
        # Si solo_activos es True, filtra los que están activos.
        if solo_activos:
            return [c for c in self.data.values() if c.activo]
        return list(self.data.values())

    def add(self, costo):
        self.data[costo.id] = costo
        return costo

    def update(self, costo):
        self.data[costo.id] = costo
        return costo

    def delete(self, id: str):
        self.data.pop(id, None)


class FakeConfiguracionRepository(ConfiguracionRepository):
    """Repositorio en memoria de configuración (pares clave -> valor).

    A diferencia de otros repositorios, aquí la clave del diccionario es la
    propia `clave` de configuración (por ejemplo "logo"), no un id.
    """

    def __init__(self) -> None:
        self.data = {}

    def get(self, clave: str):
        return self.data.get(clave)

    def set(self, clave: str, valor: str):
        # Import local: se hace aquí para evitar importaciones circulares.
        from domain.entities.configuracion import Configuracion

        c = Configuracion(clave=clave, valor=valor)
        self.data[clave] = c
        return c

    def list(self):
        return list(self.data.values())
