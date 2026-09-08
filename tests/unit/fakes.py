from domain.repositories.compra_repository import CompraRepository
from domain.repositories.producto_repository import ProductoRepository
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

    def has_for_proveedor(self, proveedor_id: str):
        return any(c.proveedor_id == proveedor_id for c in self.data.values())

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
