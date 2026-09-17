from domain.repositories.compra_repository import CompraRepository
from domain.repositories.configuracion_repository import ConfiguracionRepository
from domain.repositories.costo_fijo_repository import CostoFijoRepository
from domain.repositories.insumo_repository import InsumoRepository
from domain.repositories.producto_repository import ProductoRepository
from domain.repositories.receta_repository import RecetaRepository
from domain.repositories.usuario_repository import UsuarioRepository
from domain.repositories.venta_repository import VentaRepository


class FakeSession:
    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass

    def close(self) -> None:
        pass


class FakeProductoRepository(ProductoRepository):
    def __init__(self) -> None:
        self.data = {}

    def get(self, id: str):
        return self.data.get(id)

    def list(self, filtro=None, categoria_id=None, solo_activos=False):
        return list(self.data.values())

    def add(self, producto):
        self.data[producto.id] = producto
        return producto

    def update(self, producto):
        self.data[producto.id] = producto
        return producto


class FakeVentaRepository(VentaRepository):
    def __init__(self) -> None:
        self.data = {}

    def get(self, id: str):
        return self.data.get(id)

    def list(self, desde=None, hasta=None):
        return list(self.data.values())

    def add(self, venta):
        self.data[venta.id] = venta
        return venta

    def update(self, venta):
        self.data[venta.id] = venta
        return venta

    def delete(self, id: str):
        self.data.pop(id, None)


class FakeCompraRepository(CompraRepository):
    def __init__(self) -> None:
        self.data = {}

    def get(self, id: str):
        return self.data.get(id)

    def list(self, desde=None, hasta=None):
        return list(self.data.values())

    def add(self, compra):
        self.data[compra.id] = compra
        return compra

    def update(self, compra):
        self.data[compra.id] = compra
        return compra

    def set_detalles(self, compra_id, detalles):
        compra = self.data.get(compra_id)
        if compra is not None:
            compra.detalles = detalles

    def has_for_proveedor(self, proveedor_id: str):
        return any(c.proveedor_id == proveedor_id for c in self.data.values())

    def _suma(self, tipo, attr, valor, excluir_compra):
        total_valor = 0.0
        total_cantidad = 0.0
        for compra in self.data.values():
            if compra.anulada or compra.id == excluir_compra:
                continue
            for detalle in compra.detalles:
                if detalle.tipo == tipo and getattr(detalle, attr) == valor:
                    total_valor += detalle.cantidad * detalle.precio_unitario
                    total_cantidad += detalle.cantidad
        return total_valor, total_cantidad

    def suma_compras_insumo(self, insumo_id, excluir_compra=None):
        return self._suma("insumo", "insumo_id", insumo_id, excluir_compra)

    def suma_compras_producto(self, producto_id, excluir_compra=None):
        return self._suma("producto", "producto_id", producto_id, excluir_compra)

    def delete(self, id: str):
        self.data.pop(id, None)


class FakeUsuarioRepository(UsuarioRepository):
    def __init__(self) -> None:
        self.data = {}

    def get(self, id: str):
        return self.data.get(id)

    def get_by_email(self, email: str):
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
    def __init__(self) -> None:
        self.data = {}

    def get(self, id: str):
        return self.data.get(id)

    def list(self, filtro=None, solo_activos=False):
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
    def __init__(self) -> None:
        self.data = {}

    def list_by_producto(self, producto_id: str):
        return [d for d in self.data.values() if d.producto_id == producto_id]

    def list_all(self):
        return list(self.data.values())

    def set_for_producto(self, producto_id, detalles):
        for key in [k for k, d in self.data.items() if d.producto_id == producto_id]:
            self.data.pop(key)
        for detalle in detalles:
            self.data[detalle.id] = detalle
        return self.list_by_producto(producto_id)

    def delete_by_producto(self, producto_id: str) -> None:
        for key in [k for k, d in self.data.items() if d.producto_id == producto_id]:
            self.data.pop(key)

    def has_for_insumo(self, insumo_id: str) -> bool:
        return any(d.insumo_id == insumo_id for d in self.data.values())


class FakeCostoFijoRepository(CostoFijoRepository):
    def __init__(self) -> None:
        self.data = {}

    def get(self, id: str):
        return self.data.get(id)

    def list(self, solo_activos: bool = False):
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
    def __init__(self) -> None:
        self.data = {}

    def get(self, clave: str):
        return self.data.get(clave)

    def set(self, clave: str, valor: str):
        from domain.entities.configuracion import Configuracion

        c = Configuracion(clave=clave, valor=valor)
        self.data[clave] = c
        return c

    def list(self):
        return list(self.data.values())
