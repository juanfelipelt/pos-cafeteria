import pytest

from application.security.hashing import hash_password, verify_password
from application.services.auth_service import AuthService
from application.services.compra_service import CompraService
from application.services.venta_service import VentaService
from domain.entities.producto import Producto
from domain.exceptions import NotFoundError, UnauthorizedError, ValidationError
from tests.unit.fakes import (
    FakeCompraRepository,
    FakeProductoRepository,
    FakeSession,
    FakeUsuarioRepository,
    FakeVentaRepository,
)


def _producto(id="p1", stock=10, precio=2.0, estado=True):
    return Producto(id=id, nombre="Cafe", precio=precio, stock=stock, estado=estado)


class TestAuthService:
    def test_registrar_y_login(self):
        usuarios = FakeUsuarioRepository()
        service = AuthService(usuarios, FakeSession())

        service.registrar("Felipe", "f@x.com", "secreto")
        assert service.login("f@x.com", "secreto")

    def test_login_password_incorrecto(self):
        usuarios = FakeUsuarioRepository()
        service = AuthService(usuarios, FakeSession())
        service.registrar("Felipe", "f@x.com", "secreto")

        with pytest.raises(UnauthorizedError):
            service.login("f@x.com", "equivocada")


class TestVentaService:
    def _service(self, productos):
        return VentaService(
            FakeVentaRepository(), productos, FakeSession()
        )

    def test_crear_descuenta_stock(self):
        productos = FakeProductoRepository()
        productos.add(_producto(stock=10))
        service = self._service(productos)

        venta = service.crear([{"producto_id": "p1", "cantidad": 3}], [])
        assert productos.get("p1").stock == 7
        assert venta.total == 6.0

    def test_rechaza_stock_insuficiente(self):
        productos = FakeProductoRepository()
        productos.add(_producto(stock=2))
        service = self._service(productos)

        with pytest.raises(ValidationError):
            service.crear([{"producto_id": "p1", "cantidad": 5}], [])

    def test_rechaza_producto_inexistente(self):
        productos = FakeProductoRepository()
        service = self._service(productos)

        with pytest.raises(NotFoundError):
            service.crear([{"producto_id": "noexiste", "cantidad": 1}], [])

    def test_anular_reintegra_stock(self):
        productos = FakeProductoRepository()
        productos.add(_producto(stock=10))
        service = self._service(productos)

        venta = service.crear([{"producto_id": "p1", "cantidad": 3}], [])
        service.anular(venta.id)
        assert productos.get("p1").stock == 10


class TestCompraService:
    def _service(self, productos):
        return CompraService(
            FakeCompraRepository(), productos, FakeSession()
        )

    def test_crear_aumenta_stock(self):
        productos = FakeProductoRepository()
        productos.add(_producto(stock=5))
        service = self._service(productos)

        compra = service.crear(
            "prov1", [{"producto_id": "p1", "cantidad": 10, "precio_unitario": 1.0}]
        )
        assert productos.get("p1").stock == 15
        assert compra.total == 10.0

    def test_anular_descuenta_stock(self):
        productos = FakeProductoRepository()
        productos.add(_producto(stock=5))
        service = self._service(productos)

        compra = service.crear(
            "prov1", [{"producto_id": "p1", "cantidad": 10, "precio_unitario": 1.0}]
        )
        service.anular(compra.id)
        assert productos.get("p1").stock == 5


class TestHashing:
    def test_hash_y_verificar(self):
        h = hash_password("mi-clave")
        assert h != "mi-clave"
        assert verify_password("mi-clave", h)
        assert not verify_password("otra", h)
