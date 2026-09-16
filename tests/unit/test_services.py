import pytest

from application.security.hashing import hash_password, verify_password
from application.services.auth_service import AuthService
from application.services.compra_service import CompraService
from application.services.costeo_service import CosteoService
from application.services.venta_service import VentaService
from domain.entities.producto import Producto
from domain.exceptions import NotFoundError, UnauthorizedError, ValidationError
from tests.unit.fakes import (
    FakeCompraRepository,
    FakeConfiguracionRepository,
    FakeCostoFijoRepository,
    FakeInsumoRepository,
    FakeProductoRepository,
    FakeRecetaRepository,
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

        service.registrar("Felipe", "f@x.com", "secreto123")
        assert service.login("f@x.com", "secreto123")

    def test_login_password_incorrecto(self):
        usuarios = FakeUsuarioRepository()
        service = AuthService(usuarios, FakeSession())
        service.registrar("Felipe", "f@x.com", "secreto123")

        with pytest.raises(UnauthorizedError):
            service.login("f@x.com", "equivocada")


class TestVentaService:
    def _service(self, productos, insumos=None, recetas=None):
        return VentaService(
            FakeVentaRepository(),
            productos,
            insumos or FakeInsumoRepository(),
            recetas or FakeRecetaRepository(),
            FakeSession(),
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

    def test_guarda_costo_y_consume_insumo(self):
        from domain.entities.detalle_receta import DetalleReceta
        from domain.entities.insumo import Insumo
        from domain.entities.producto import Producto

        insumos = FakeInsumoRepository()
        insumos.add(
            Insumo(id="i1", nombre="Cafe", unidad="g", stock=1000, costo_unitario=2.0)
        )
        recetas = FakeRecetaRepository()
        recetas.data["r1"] = DetalleReceta(
            id="r1", producto_id="p1", insumo_id="i1", cantidad=10
        )
        productos = FakeProductoRepository()
        productos.add(
            Producto(
                id="p1",
                nombre="Capuchino",
                precio=5.0,
                stock=10,
                tipo="preparado",
            )
        )
        service = self._service(productos, insumos, recetas)

        venta = service.crear([{"producto_id": "p1", "cantidad": 3}], [])
        assert venta.detalles[0].costo_unitario == 20.0
        assert productos.get("p1").stock == 7
        assert insumos.get("i1").stock == 970.0

        service.anular(venta.id)
        assert productos.get("p1").stock == 10
        assert insumos.get("i1").stock == 1000.0


class TestCompraService:
    def _service(self, productos, insumos=None):
        return CompraService(
            FakeCompraRepository(),
            productos,
            insumos or FakeInsumoRepository(),
            FakeSession(),
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

    def test_crear_insumo_promedio_ponderado(self):
        from domain.entities.insumo import Insumo

        insumos = FakeInsumoRepository()
        insumos.add(Insumo(id="i1", nombre="Cafe", unidad="g", stock=100, costo_unitario=2.0))
        service = self._service(FakeProductoRepository(), insumos)

        service.crear(
            "prov1", [{"tipo": "insumo", "insumo_id": "i1", "cantidad": 100, "precio_unitario": 4.0}]
        )
        insumo = insumos.get("i1")
        assert insumo.stock == 200
        assert insumo.costo_unitario == 3.0

    def test_anular_compra_revierte_costo(self):
        from domain.entities.insumo import Insumo

        insumos = FakeInsumoRepository()
        insumos.add(Insumo(id="i1", nombre="Cafe", unidad="g", stock=100, costo_unitario=2.0))
        service = self._service(FakeProductoRepository(), insumos)

        service.crear(
            "prov1", [{"tipo": "insumo", "insumo_id": "i1", "cantidad": 100, "precio_unitario": 2.0}]
        )
        compra2 = service.crear(
            "prov1", [{"tipo": "insumo", "insumo_id": "i1", "cantidad": 100, "precio_unitario": 4.0}]
        )
        assert round(insumos.get("i1").costo_unitario, 3) == 2.667

        # Recalcula desde el historial (quedan 100 g @ 2.0), no la fórmula aditiva.
        service.anular(compra2.id)
        assert insumos.get("i1").stock == 200
        assert insumos.get("i1").costo_unitario == 2.0

    def test_anular_compra_exacto_con_consumo(self):
        from domain.entities.insumo import Insumo

        insumos = FakeInsumoRepository()
        insumos.add(Insumo(id="i1", nombre="Cafe", unidad="g"))
        service = self._service(FakeProductoRepository(), insumos)

        compra1 = service.crear(
            "prov1", [{"tipo": "insumo", "insumo_id": "i1", "cantidad": 100, "precio_unitario": 2.0}]
        )
        # Consumo (como si se hubieran vendido productos): 50 g
        insumo = insumos.get("i1")
        insumo.stock -= 50
        insumos.update(insumo)

        service.crear(
            "prov1", [{"tipo": "insumo", "insumo_id": "i1", "cantidad": 100, "precio_unitario": 4.0}]
        )
        # Anular la PRIMERA compra: queda la de 4.0 => costo 4.0 (exacto)
        service.anular(compra1.id)
        assert insumos.get("i1").costo_unitario == 4.0


class TestHashing:
    def test_hash_y_verificar(self):
        h = hash_password("mi-clave")
        assert h != "mi-clave"
        assert verify_password("mi-clave", h)
        assert not verify_password("otra", h)


class TestCosteoService:
    def _service(self, productos=None, ventas=None, costos=None):
        return CosteoService(
            productos or FakeProductoRepository(),
            FakeInsumoRepository(),
            FakeRecetaRepository(),
            costos or FakeCostoFijoRepository(),
            FakeConfiguracionRepository(),
            ventas or FakeVentaRepository(),
            FakeSession(),
        )

    def test_costo_fijo_periodo_cruza_meses(self):
        from datetime import date

        service = self._service()
        dias = {1, 2, 3, 4, 5, 6}
        total = service._costo_fijo_periodo(
            260000.0, dias, date(2024, 6, 1), date(2024, 7, 5)
        )
        jun = service._contar_dias(dias, date(2024, 6, 1), date(2024, 6, 30))
        jul = service._contar_dias(dias, date(2024, 7, 1), date(2024, 7, 5))
        jul_mes = service._contar_dias(dias, date(2024, 7, 1), date(2024, 7, 31))
        esperado = 260000.0 + 260000.0 * jul / jul_mes
        assert abs(total - esperado) < 1e-6
        assert jun > 0

    def test_resumen_usa_costo_guardado(self):
        from datetime import datetime, timedelta

        from domain.entities.detalle_venta import DetalleVenta
        from domain.entities.venta import Venta

        productos = FakeProductoRepository()
        productos.add(Producto(id="p1", nombre="Cafe", precio=5.0, stock=100, costo=1.0))
        ventas = FakeVentaRepository()
        ventas.add(
            Venta(
                id="v1",
                detalles=[
                    DetalleVenta(
                        producto_id="p1",
                        nombre_producto="Cafe",
                        cantidad=2,
                        precio_unitario=5.0,
                        costo_unitario=3.0,
                    )
                ],
            )
        )
        service = self._service(productos=productos, ventas=ventas)
        ahora = datetime.now()
        resumen = service.resumen(
            ahora - timedelta(days=1), ahora + timedelta(days=1)
        )
        assert resumen["ventas"] == 10.0
        assert resumen["costo_variable"] == 6.0
