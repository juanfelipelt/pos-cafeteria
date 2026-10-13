"""Pruebas unitarias de los SERVICIOS de la aplicación.

Los servicios contienen la lógica de negocio (crear ventas, compras, costear,
autenticar, etc.) y trabajan contra repositorios. Para probarlos de forma rápida
y aislada usamos los "fakes" de tests/unit/fakes.py en lugar de una base de
datos real.

Cada prueba sigue el patrón arrange (preparar), act (ejecutar) y assert
(comprobar), y verifica los resultados y sus efectos secundarios: descuento de
stock, cálculo de costos, reintegro de stock al anular, etc.
"""

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
    """Helper: crea un Producto de prueba con valores por defecto.

    Por defecto: 10 unidades en stock, precio 2.0 y activo.
    """
    return Producto(id=id, nombre="Cafe", precio=precio, stock=stock, estado=estado)


class TestAuthService:
    """Prueba el registro y el login de usuarios (servicio de autenticación)."""

    def test_registrar_y_login(self):
        """Tras registrar un usuario, se puede iniciar sesión con su contraseña."""
        # arrange: repositorio fake de usuarios y servicio de autenticación.
        usuarios = FakeUsuarioRepository()
        service = AuthService(usuarios, FakeSession())

        # act: registramos un usuario.
        service.registrar("Felipe", "f@x.com", "secreto123")
        # assert: el login con esas credenciales es exitoso.
        assert service.login("f@x.com", "secreto123")

    def test_login_password_incorrecto(self):
        """Si la contraseña es incorrecta, el login lanza UnauthorizedError."""
        # arrange: usuario ya registrado.
        usuarios = FakeUsuarioRepository()
        service = AuthService(usuarios, FakeSession())
        service.registrar("Felipe", "f@x.com", "secreto123")

        # act + assert: login con contraseña equivocada debe fallar.
        with pytest.raises(UnauthorizedError):
            service.login("f@x.com", "equivocada")


class TestVentaService:
    """Prueba la creación y anulación de ventas, y sus efectos en el stock."""

    def _service(self, productos, insumos=None, recetas=None):
        """Helper: arma un VentaService con repositorios fake.

        Permite inyectar los repositorios de productos, insumos y recetas que
        necesitemos para cada prueba.
        """
        return VentaService(
            FakeVentaRepository(),
            productos,
            insumos or FakeInsumoRepository(),
            recetas or FakeRecetaRepository(),
            FakeSession(),
        )

    def test_crear_descuenta_stock(self):
        """Al crear una venta se descuenta el stock y se calcula el total."""
        # arrange: producto con 10 unidades y servicio de ventas.
        productos = FakeProductoRepository()
        productos.add(_producto(stock=10))
        service = self._service(productos)

        # act: vendemos 3 unidades.
        venta = service.crear([{"producto_id": "p1", "cantidad": 3}], [])
        # assert: quedan 7 en stock y el total es 3 × 2.0 = 6.0.
        assert productos.get("p1").stock == 7
        assert venta.total == 6.0

    def test_rechaza_stock_insuficiente(self):
        """Vender más unidades que el stock disponible lanza ValidationError."""
        # arrange: producto con solo 2 unidades.
        productos = FakeProductoRepository()
        productos.add(_producto(stock=2))
        service = self._service(productos)

        # act + assert: intentar vender 5 unidades debe fallar.
        with pytest.raises(ValidationError):
            service.crear([{"producto_id": "p1", "cantidad": 5}], [])

    def test_rechaza_producto_inexistente(self):
        """Vender un producto que no existe lanza NotFoundError."""
        # arrange: repositorio de productos vacío.
        productos = FakeProductoRepository()
        service = self._service(productos)

        # act + assert: vender un id inexistente debe fallar.
        with pytest.raises(NotFoundError):
            service.crear([{"producto_id": "noexiste", "cantidad": 1}], [])

    def test_anular_reintegra_stock(self):
        """Anular una venta devuelve las unidades vendidas al stock."""
        # arrange: producto con 10 unidades.
        productos = FakeProductoRepository()
        productos.add(_producto(stock=10))
        service = self._service(productos)

        # act: vendemos 3 (quedan 7) y luego anulamos la venta.
        venta = service.crear([{"producto_id": "p1", "cantidad": 3}], [])
        service.anular(venta.id)
        # assert: el stock vuelve a 10.
        assert productos.get("p1").stock == 10

    def test_guarda_costo_y_consume_insumo(self):
        """Un producto preparado consume insumos y guarda su costo unitario.

        Al vender, se descuenta el stock del producto y se consumen los insumos
        de su receta; además, la venta guarda el costo calculado. Al anular, se
        reintegra tanto el producto como los insumos.
        """
        from domain.entities.detalle_receta import DetalleReceta
        from domain.entities.insumo import Insumo
        from domain.entities.producto import Producto

        # arrange: insumo "Cafe" (1000 g a 2.0) y receta que usa 10 g por unidad.
        insumos = FakeInsumoRepository()
        insumos.add(
            Insumo(id="i1", nombre="Cafe", unidad="g", stock=1000, costo_unitario=2.0)
        )
        recetas = FakeRecetaRepository()
        recetas.data["r1"] = DetalleReceta(
            id="r1", producto_id="p1", insumo_id="i1", cantidad=10
        )
        # arrange: producto preparado "Capuchino" (precio 5.0, stock 10).
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

        # act: vendemos 3 capuchinos.
        venta = service.crear([{"producto_id": "p1", "cantidad": 3}], [])
        # assert: costo unitario = 10 g × 2.0 = 20.0; producto 10-3=7; insumo 1000-30=970.
        assert venta.detalles[0].costo_unitario == 20.0
        assert productos.get("p1").stock == 7
        assert insumos.get("i1").stock == 970.0

        # act: anulamos la venta.
        service.anular(venta.id)
        # assert: se reintegran tanto el producto como el insumo.
        assert productos.get("p1").stock == 10
        assert insumos.get("i1").stock == 1000.0


class TestCompraService:
    """Prueba la creación y anulación de compras, y el costo promedio ponderado."""

    def _service(self, productos, insumos=None):
        """Helper: arma un CompraService con repositorios fake.

        Permite inyectar los repositorios de productos e insumos necesarios.
        """
        return CompraService(
            FakeCompraRepository(),
            productos,
            insumos or FakeInsumoRepository(),
            FakeSession(),
        )

    def test_crear_aumenta_stock(self):
        """Al registrar una compra, el stock del producto aumenta."""
        # arrange: producto con 5 unidades.
        productos = FakeProductoRepository()
        productos.add(_producto(stock=5))
        service = self._service(productos)

        # act: compramos 10 unidades a 1.0.
        compra = service.crear(
            "prov1", [{"producto_id": "p1", "cantidad": 10, "precio_unitario": 1.0}]
        )
        # assert: stock 5+10=15 y total 10.0.
        assert productos.get("p1").stock == 15
        assert compra.total == 10.0

    def test_anular_descuenta_stock(self):
        """Anular una compra resta del stock las unidades que había sumado."""
        # arrange: producto con 5 unidades.
        productos = FakeProductoRepository()
        productos.add(_producto(stock=5))
        service = self._service(productos)

        # act: compramos 10 (stock 15) y luego anulamos la compra.
        compra = service.crear(
            "prov1", [{"producto_id": "p1", "cantidad": 10, "precio_unitario": 1.0}]
        )
        service.anular(compra.id)
        # assert: el stock vuelve a 5.
        assert productos.get("p1").stock == 5

    def test_crear_insumo_promedio_ponderado(self):
        """Comprar un insumo recalcula su costo con promedio ponderado."""
        from domain.entities.insumo import Insumo

        # arrange: insumo con 100 g a 2.0 de costo.
        insumos = FakeInsumoRepository()
        insumos.add(Insumo(id="i1", nombre="Cafe", unidad="g", stock=100, costo_unitario=2.0))
        service = self._service(FakeProductoRepository(), insumos)

        # act: compramos 100 g más a 4.0.
        service.crear(
            "prov1", [{"tipo": "insumo", "insumo_id": "i1", "cantidad": 100, "precio_unitario": 4.0}]
        )
        # assert: stock 200 y costo (100×2 + 100×4)/200 = 3.0.
        insumo = insumos.get("i1")
        assert insumo.stock == 200
        assert insumo.costo_unitario == 3.0

    def test_anular_compra_revierte_costo(self):
        """Anular una compra recalcula el costo del insumo desde el historial."""
        from domain.entities.insumo import Insumo

        # arrange: insumo con 100 g a 2.0.
        insumos = FakeInsumoRepository()
        insumos.add(Insumo(id="i1", nombre="Cafe", unidad="g", stock=100, costo_unitario=2.0))
        service = self._service(FakeProductoRepository(), insumos)

        # act: dos compras de 100 g (a 2.0 y a 4.0) => costo ponderado 3.0.
        service.crear(
            "prov1", [{"tipo": "insumo", "insumo_id": "i1", "cantidad": 100, "precio_unitario": 2.0}]
        )
        compra2 = service.crear(
            "prov1", [{"tipo": "insumo", "insumo_id": "i1", "cantidad": 100, "precio_unitario": 4.0}]
        )
        assert round(insumos.get("i1").costo_unitario, 3) == 2.667

        # Recalcula desde el historial (quedan 100 g @ 2.0), no la fórmula aditiva.
        # act: anulamos la segunda compra.
        service.anular(compra2.id)
        # assert: stock de vuelta en 200 y costo exacto en 2.0.
        assert insumos.get("i1").stock == 200
        assert insumos.get("i1").costo_unitario == 2.0

    def test_anular_compra_exacto_con_consumo(self):
        """El costo se recalcula con exactitud aunque haya consumo de insumo.

        Este caso simula que parte del insumo ya se consumió (se vendió): al
        anular una compra, el costo debe corresponder al historial restante.
        """
        from domain.entities.insumo import Insumo

        # arrange: insumo vacío.
        insumos = FakeInsumoRepository()
        insumos.add(Insumo(id="i1", nombre="Cafe", unidad="g"))
        service = self._service(FakeProductoRepository(), insumos)

        # act: primera compra de 100 g a 2.0.
        compra1 = service.crear(
            "prov1", [{"tipo": "insumo", "insumo_id": "i1", "cantidad": 100, "precio_unitario": 2.0}]
        )
        # Consumo (como si se hubieran vendido productos): 50 g
        insumo = insumos.get("i1")
        insumo.stock -= 50
        insumos.update(insumo)

        # act: segunda compra de 100 g a 4.0.
        service.crear(
            "prov1", [{"tipo": "insumo", "insumo_id": "i1", "cantidad": 100, "precio_unitario": 4.0}]
        )
        # Anular la PRIMERA compra: queda la de 4.0 => costo 4.0 (exacto)
        service.anular(compra1.id)
        # assert: el costo unitario queda exactamente en 4.0.
        assert insumos.get("i1").costo_unitario == 4.0


class TestHashing:
    """Prueba el hasheo y la verificación de contraseñas."""

    def test_hash_y_verificar(self):
        """El hash no debe ser igual a la clave y debe poder verificarse."""
        # act: generamos el hash de una contraseña.
        h = hash_password("mi-clave")
        # assert: el hash no expone la contraseña original.
        assert h != "mi-clave"
        # assert: verificar la clave correcta da True y la incorrecta da False.
        assert verify_password("mi-clave", h)
        assert not verify_password("otra", h)


class TestCosteoService:
    """Prueba el cálculo de costos fijos y el resumen de costeo."""

    def _service(self, productos=None, ventas=None, costos=None):
        """Helper: arma un CosteoService con repositorios fake.

        Permite inyectar productos, ventas y costos fijos; el resto queda vacío.
        """
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
        """El costo fijo de un período se prorratea aunque cruce dos meses."""
        from datetime import date

        # arrange: servicio y un conjunto de días laborables {1..6}.
        service = self._service()
        dias = {1, 2, 3, 4, 5, 6}
        # act: calculamos el costo fijo para un período de junio a julio.
        total = service._costo_fijo_periodo(
            260000.0, dias, date(2024, 6, 1), date(2024, 7, 5)
        )
        # Calculamos los días laborables de cada mes para reconstruir lo esperado.
        jun = service._contar_dias(dias, date(2024, 6, 1), date(2024, 6, 30))
        jul = service._contar_dias(dias, date(2024, 7, 1), date(2024, 7, 5))
        jul_mes = service._contar_dias(dias, date(2024, 7, 1), date(2024, 7, 31))
        esperado = 260000.0 + 260000.0 * jul / jul_mes
        # assert: el prorrateo coincide (junio completo + parte proporcional de julio).
        assert abs(total - esperado) < 1e-6
        assert jun > 0

    def test_resumen_usa_costo_guardado(self):
        """El resumen usa el costo guardado en cada detalle, no el del producto."""
        from datetime import datetime, timedelta

        from domain.entities.detalle_venta import DetalleVenta
        from domain.entities.venta import Venta

        # arrange: producto con costo 1.0, pero el detalle vendido tiene costo 3.0.
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
        # act: pedimos el resumen de un rango que incluye la venta.
        ahora = datetime.now()
        resumen = service.resumen(
            ahora - timedelta(days=1), ahora + timedelta(days=1)
        )
        # assert: ventas 2×5.0=10.0 y costo variable 2×3.0=6.0 (usa el costo guardado).
        assert resumen["ventas"] == 10.0
        assert resumen["costo_variable"] == 6.0
