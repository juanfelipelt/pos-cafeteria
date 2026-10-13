"""Pruebas de integración del módulo de costeo (insumos, recetas y costos).

Estas pruebas verifican, a través de la API real (TestClient + SQLite temporal),
cómo se calculan y actualizan los costos: costo de insumos con promedio
ponderado, costo de recetas, productos comprados y compuestos, costos fijos y el
resumen de costeo con punto de equilibrio.

Se usan helpers para crear insumos y productos, y se sigue el patrón
arrange/act/assert en cada prueba.
"""

from datetime import datetime, timedelta


def _rango_hoy():
    """Helper: devuelve (desde, hasta) como el día de hoy completo.

    `desde` es la medianoche de hoy y `hasta` es el último instante del día, en
    formato ISO, para usarlos como filtros de fecha en la API.
    """
    ahora = datetime.now()
    desde = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    hasta = desde + timedelta(days=1) - timedelta(microseconds=1)
    return desde.isoformat(), hasta.isoformat()


def _create_insumo(client, headers, nombre="Cafe", unidad="g", stock=0.0, costo=0.0):
    """Helper: crea un insumo vía API y devuelve su JSON.

    Por defecto: nombre "Cafe", unidad "g", stock 0 y costo 0. Falla si la API
    no responde 200.
    """
    r = client.post(
        "/insumos",
        json={
            "nombre": nombre,
            "unidad": unidad,
            "stock": stock,
            "costo_unitario": costo,
        },
        headers=headers,
    )
    # assert: el insumo debe crearse correctamente.
    assert r.status_code == 200, r.text
    return r.json()


def _create_producto(
    client, headers, nombre="Capuchino", precio=5.0, tipo="preparado", stock=0
):
    """Helper: crea un producto vía API y devuelve su JSON.

    Por defecto: "Capuchino", precio 5.0, tipo "preparado" y stock 0. Falla si
    la API no responde 200.
    """
    r = client.post(
        "/productos",
        json={"nombre": nombre, "precio": precio, "stock": stock, "tipo": tipo},
        headers=headers,
    )
    # assert: el producto debe crearse correctamente.
    assert r.status_code == 200, r.text
    return r.json()


class TestInsumos:
    """Prueba el CRUD de insumos y sus validaciones de permisos y datos."""

    def test_crud(self, client, admin_headers):
        """Crea, lista, edita costo, cambia estado y elimina un insumo."""
        # arrange: creamos un insumo con 100 g a 2.0.
        insumo = _create_insumo(client, admin_headers, stock=100, costo=2.0)
        assert insumo["nombre"] == "Cafe"
        assert insumo["unidad"] == "g"

        # act + assert: lo listamos y debe haber exactamente uno.
        r = client.get("/insumos", headers=admin_headers)
        assert r.status_code == 200
        assert len(r.json()) == 1

        # act + assert: actualizamos su costo a 3.0.
        r = client.put(
            f"/insumos/{insumo['id']}",
            json={"costo_unitario": 3.0},
            headers=admin_headers,
        )
        assert r.json()["costo_unitario"] == 3.0

        # act + assert: lo desactivamos.
        r = client.patch(
            f"/insumos/{insumo['id']}/estado",
            json={"estado": False},
            headers=admin_headers,
        )
        assert r.json()["estado"] is False

        # act + assert: lo eliminamos correctamente.
        r = client.delete(f"/insumos/{insumo['id']}", headers=admin_headers)
        assert r.status_code == 200

    def test_crear_requiere_admin(self, client, cajero_headers):
        """Un cajero no puede crear insumos (403)."""
        # act: el cajero intenta crear un insumo.
        r = client.post(
            "/insumos",
            json={"nombre": "X", "unidad": "g"},
            headers=cajero_headers,
        )
        # assert: prohibido para cajero.
        assert r.status_code == 403

    def test_nombre_y_unidad_obligatorios(self, client, admin_headers):
        """El nombre no puede venir vacío (422 de validación)."""
        # act + assert: nombre vacío debe fallar con 422.
        r = client.post(
            "/insumos", json={"nombre": "", "unidad": "g"}, headers=admin_headers
        )
        assert r.status_code == 422


class TestReceta:
    """Prueba la asignación de recetas a productos y el cálculo de su costo."""

    def test_receta_calcula_costo(self, client, admin_headers):
        """La receta de un producto definen su costo y margen."""
        # arrange: insumo a 2.0 y producto preparado "Capuchino".
        insumo = _create_insumo(client, admin_headers, stock=1000, costo=2.0)
        producto = _create_producto(client, admin_headers)

        # act: la receta usa 10 g del insumo => costo 20.0.
        r = client.put(
            f"/productos/{producto['id']}/receta",
            json={"items": [{"insumo_id": insumo["id"], "cantidad": 10}]},
            headers=admin_headers,
        )
        # assert: el subtotal de la receta es 10 × 2.0 = 20.0.
        assert r.status_code == 200
        assert r.json()[0]["subtotal"] == 20.0

        # act + assert: el reporte de costeo refleja costo 20.0 y margen 5.0-20.0.
        r = client.get("/costeo/productos", headers=admin_headers)
        assert r.status_code == 200
        fila = next(f for f in r.json() if f["producto_id"] == producto["id"])
        assert fila["costo"] == 20.0
        assert fila["margen"] == producto["precio"] - 20.0

    def test_receta_solo_preparado(self, client, admin_headers):
        """Solo los productos preparados pueden tener receta (un comprado no)."""
        # arrange: un insumo y un producto de tipo "comprado".
        insumo = _create_insumo(client, admin_headers)
        producto = _create_producto(
            client, admin_headers, nombre="Gaseosa", tipo="comprado"
        )
        # act + assert: asignar receta a un comprado debe fallar (422).
        r = client.put(
            f"/productos/{producto['id']}/receta",
            json={"items": [{"insumo_id": insumo["id"], "cantidad": 1}]},
            headers=admin_headers,
        )
        assert r.status_code == 422


class TestCompraInsumo:
    """Prueba las compras de insumos: stock, costo ponderado y edición."""

    def _proveedor(self, client, headers):
        """Helper: crea un proveedor de prueba y devuelve su JSON."""
        return client.post(
            "/proveedores",
            json={"nombre": "Prov", "contacto": "X", "telefono": "1"},
            headers=headers,
        ).json()

    def test_promedio_ponderado(self, client, admin_headers):
        """Comprar un insumo recalcula su costo con promedio ponderado."""
        # arrange: proveedor e insumo con 100 g a 2.0.
        prov = self._proveedor(client, admin_headers)
        insumo = _create_insumo(client, admin_headers, stock=100, costo=2.0)

        # act: compramos 100 g a 4.0.
        r = client.post(
            "/compras",
            json={
                "proveedor_id": prov["id"],
                "items": [
                    {
                        "tipo": "insumo",
                        "insumo_id": insumo["id"],
                        "cantidad": 100,
                        "precio_unitario": 4.0,
                    }
                ],
            },
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text

        # assert: stock 200 y costo (100×2 + 100×4)/200 = 3.0.
        r = client.get(f"/insumos/{insumo['id']}", headers=admin_headers)
        assert r.json()["stock"] == 200
        assert r.json()["costo_unitario"] == 3.0

    def test_editar_compra_ajusta_stock_y_costo(self, client, admin_headers):
        """Editar una compra ajusta el stock y recalcula el costo del insumo."""
        # arrange: proveedor e insumo vacío.
        prov = self._proveedor(client, admin_headers)
        insumo = _create_insumo(
            client, admin_headers, stock=0, costo=0
        )
        # Creamos dos compras: 100 g a 2.0 y 100 g a 4.0.
        client.post(
            "/compras",
            json={
                "proveedor_id": prov["id"],
                "items": [
                    {"tipo": "insumo", "insumo_id": insumo["id"], "cantidad": 100, "precio_unitario": 2.0}
                ],
            },
            headers=admin_headers,
        )
        r = client.post(
            "/compras",
            json={
                "proveedor_id": prov["id"],
                "items": [
                    {"tipo": "insumo", "insumo_id": insumo["id"], "cantidad": 100, "precio_unitario": 4.0}
                ],
            },
            headers=admin_headers,
        )
        compra_b = r.json()

        # Editar la 2ª compra: 100 @ 10
        # act: cambiamos el precio de la segunda compra a 10.0.
        r = client.put(
            f"/compras/{compra_b['id']}",
            json={
                "proveedor_id": prov["id"],
                "items": [
                    {"tipo": "insumo", "insumo_id": insumo["id"], "cantidad": 100, "precio_unitario": 10.0}
                ],
            },
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text

        # assert: stock sigue en 200 y el costo se recalcula.
        ins = client.get(f"/insumos/{insumo['id']}", headers=admin_headers).json()
        assert ins["stock"] == 200
        # (100×2 + 100×10) / 200 = 6.0
        assert ins["costo_unitario"] == 6.0

    def test_editar_compra_requiere_admin(self, client, admin_headers, cajero_headers):
        """Un cajero no puede editar compras (403)."""
        # arrange: proveedor, insumo y una compra creada por el admin.
        prov = self._proveedor(client, admin_headers)
        insumo = _create_insumo(client, admin_headers, stock=0, costo=0)
        compra = client.post(
            "/compras",
            json={
                "proveedor_id": prov["id"],
                "items": [
                    {"tipo": "insumo", "insumo_id": insumo["id"], "cantidad": 10, "precio_unitario": 1.0}
                ],
            },
            headers=admin_headers,
        ).json()

        # act: el cajero intenta editar la compra.
        r = client.put(
            f"/compras/{compra['id']}",
            json={
                "proveedor_id": prov["id"],
                "items": [
                    {"tipo": "insumo", "insumo_id": insumo["id"], "cantidad": 20, "precio_unitario": 1.0}
                ],
            },
            headers=cajero_headers,
        )
        # assert: prohibido para cajero.
        assert r.status_code == 403

    def test_editar_compra_anulada(self, client, admin_headers):
        """No se puede editar una compra que ya fue anulada (422)."""
        # arrange: proveedor, insumo y una compra que anulamos.
        prov = self._proveedor(client, admin_headers)
        insumo = _create_insumo(client, admin_headers, stock=0, costo=0)
        compra = client.post(
            "/compras",
            json={
                "proveedor_id": prov["id"],
                "items": [
                    {"tipo": "insumo", "insumo_id": insumo["id"], "cantidad": 10, "precio_unitario": 1.0}
                ],
            },
            headers=admin_headers,
        ).json()
        client.post(f"/compras/{compra['id']}/anular", headers=admin_headers)

        # act: intentamos editarla estando anulada.
        r = client.put(
            f"/compras/{compra['id']}",
            json={
                "proveedor_id": prov["id"],
                "items": [
                    {"tipo": "insumo", "insumo_id": insumo["id"], "cantidad": 20, "precio_unitario": 1.0}
                ],
            },
            headers=admin_headers,
        )
        # assert: la API responde 422.
        assert r.status_code == 422


class TestCostosFijos:
    """Prueba el CRUD de costos fijos (arriendo, servicios, etc.)."""

    def test_crud(self, client, admin_headers):
        """Crea, lista, edita y elimina un costo fijo."""
        # act: creamos el costo fijo "Arriendo" por 1.000.000.
        r = client.post(
            "/costos-fijos",
            json={"nombre": "Arriendo", "monto": 1000000},
            headers=admin_headers,
        )
        assert r.status_code == 200
        costo = r.json()

        # act + assert: lo listamos y debe haber uno.
        r = client.get("/costos-fijos", headers=admin_headers)
        assert len(r.json()) == 1

        # act + assert: editamos el monto a 1.200.000.
        r = client.put(
            f"/costos-fijos/{costo['id']}",
            json={"monto": 1200000},
            headers=admin_headers,
        )
        assert r.json()["monto"] == 1200000

        # act + assert: lo eliminamos correctamente.
        r = client.delete(f"/costos-fijos/{costo['id']}", headers=admin_headers)
        assert r.status_code == 200


class TestCosteoResumen:
    """Prueba el resumen de costeo: ventas, margen, costos fijos y equilibrio."""

    def test_resumen_con_venta(self, client, admin_headers):
        """El resumen calcula ventas, costo variable, margen y punto de equilibrio."""
        # arrange: insumo a 1.0, producto a 5.0 con receta de 2 g y costo fijo.
        insumo = _create_insumo(client, admin_headers, stock=1000, costo=1.0)
        producto = _create_producto(client, admin_headers, precio=5.0, stock=10)
        client.put(
            f"/productos/{producto['id']}/receta",
            json={"items": [{"insumo_id": insumo["id"], "cantidad": 2}]},
            headers=admin_headers,
        )
        client.post(
            "/costos-fijos",
            json={"nombre": "Arriendo", "monto": 260000},
            headers=admin_headers,
        )
        # act: vendemos 3 unidades (sin pagos).
        r = client.post(
            "/ventas",
            json={"items": [{"producto_id": producto["id"], "cantidad": 3}], "pagos": []},
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text

        # act: pedimos el resumen del día de hoy.
        desde, hasta = _rango_hoy()
        r = client.get(
            f"/costeo/resumen?desde={desde}&hasta={hasta}",
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        # assert: ventas 3×5=15, costo variable 3×2=6, margen 9, y datos del período.
        assert data["ventas"] == 15.0
        assert data["costo_variable"] == 6.0
        assert data["margen"] == 9.0
        assert data["costos_fijos_mes"] == 260000
        assert data["dias_laborables_mes"] > 0
        assert data["punto_equilibrio"] is not None

    def test_resumen_requiere_admin(self, client, cajero_headers):
        """Un cajero no puede ver el resumen de costeo (403)."""
        # act + assert: consultar el resumen está prohibido para cajero.
        desde, hasta = _rango_hoy()
        r = client.get(
            f"/costeo/resumen?desde={desde}&hasta={hasta}",
            headers=cajero_headers,
        )
        assert r.status_code == 403

    def test_resumen_prorratea_mes(self, client, admin_headers):
        """El costo fijo del período se prorratea cuando el rango no es un mes completo."""
        # arrange: un costo fijo mensual de 260.000.
        client.post(
            "/costos-fijos",
            json={"nombre": "Arriendo", "monto": 260000},
            headers=admin_headers,
        )
        # act: pedimos el resumen de un rango que cruza junio y parte de julio.
        r = client.get(
            "/costeo/resumen?desde=2024-06-01T00:00:00"
            "&hasta=2024-07-05T23:59:59",
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        # assert: el costo fijo mensual es 260.000 y el del período queda entre
        # un mes y dos meses (junio completo + prorrateo de julio).
        assert data["costos_fijos_mes"] == 260000
        assert 260000 <= data["costo_fijo_periodo"] <= 520000

    def test_venta_guarda_costo_y_descuenta_insumo(self, client, admin_headers):
        """Una venta guarda el costo unitario y descuenta el insumo de la receta."""
        # arrange: insumo a 1.0 y producto con receta de 2 g por unidad.
        insumo = _create_insumo(client, admin_headers, stock=1000, costo=1.0)
        producto = _create_producto(client, admin_headers, precio=5.0, stock=10)
        client.put(
            f"/productos/{producto['id']}/receta",
            json={"items": [{"insumo_id": insumo["id"], "cantidad": 2}]},
            headers=admin_headers,
        )
        # act: vendemos 3 unidades.
        r = client.post(
            "/ventas",
            json={"items": [{"producto_id": producto["id"], "cantidad": 3}], "pagos": []},
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text
        venta = r.json()
        # assert: la venta guarda el costo unitario 2 g × 1.0 = 2.0.
        assert venta["detalles"][0]["costo_unitario"] == 2.0

        # assert: el insumo baja de 1000 a 994 (se usaron 2 g × 3 = 6 g).
        r = client.get(f"/insumos/{insumo['id']}", headers=admin_headers)
        assert r.json()["stock"] == 994.0  # 1000 - 2*3


class TestCostoProductoComprado:
    """Prueba el costo de un producto comprado (no preparado)."""

    def test_costo_no_se_diluye_con_stock_sin_costo(self, client, admin_headers):
        """El costo de un producto comprado no se diluye con stock sin costo."""
        # arrange: proveedor y producto "Agua" de tipo comprado con stock 1.
        prov = client.post(
            "/proveedores",
            json={"nombre": "Prov", "contacto": "X", "telefono": "1"},
            headers=admin_headers,
        ).json()
        producto = client.post(
            "/productos",
            json={"nombre": "Agua", "precio": 3000, "stock": 1, "tipo": "comprado"},
            headers=admin_headers,
        ).json()

        # act: compramos 1 unidad a 1200.
        client.post(
            "/compras",
            json={
                "proveedor_id": prov["id"],
                "items": [
                    {
                        "tipo": "producto",
                        "producto_id": producto["id"],
                        "cantidad": 1,
                        "precio_unitario": 1200,
                    }
                ],
            },
            headers=admin_headers,
        )

        # assert: el costo del producto queda en 1200 (no se diluye).
        p = client.get(f"/productos/{producto['id']}", headers=admin_headers).json()
        assert p["costo"] == 1200.0

        # act + assert: el reporte de costeo muestra costo 1200 y margen 1800.
        r = client.get("/costeo/productos", headers=admin_headers)
        fila = next(f for f in r.json() if f["producto_id"] == producto["id"])
        assert fila["costo"] == 1200.0
        assert fila["margen"] == 1800.0


class TestProductoCompuesto:
    """Prueba los productos "combo" (compuestos por otros productos o insumos)."""

    def _proveedor(self, client, headers):
        """Helper: crea un proveedor de prueba y devuelve su JSON."""
        return client.post(
            "/proveedores",
            json={"nombre": "Prov", "contacto": "X", "telefono": "1"},
            headers=headers,
        ).json()

    def test_combo_costo_y_consumo(self, client, admin_headers):
        """Un combo calcula su costo y consume los componentes al venderse."""
        # arrange: proveedor, insumo "Papa" y producto "Papa Frita" con receta.
        prov = self._proveedor(client, admin_headers)
        papa_insumo = _create_insumo(
            client, admin_headers, nombre="Papa", unidad="g", stock=10000, costo=1.0
        )
        papa = _create_producto(
            client, admin_headers, nombre="Papa Frita", precio=4.0, tipo="preparado", stock=100
        )
        client.put(
            f"/productos/{papa['id']}/receta",
            json={"items": [{"tipo": "insumo", "insumo_id": papa_insumo["id"], "cantidad": 10}]},
            headers=admin_headers,
        )

        # arrange: producto comprado "Coca Cola" y una compra de 100 a 2.0.
        coca = _create_producto(
            client, admin_headers, nombre="Coca Cola", precio=3.0, tipo="comprado", stock=0
        )
        client.post(
            "/compras",
            json={
                "proveedor_id": prov["id"],
                "items": [
                    {
                        "tipo": "producto",
                        "producto_id": coca["id"],
                        "cantidad": 100,
                        "precio_unitario": 2.0,
                    }
                ],
            },
            headers=admin_headers,
        )

        # arrange: combo de papa + coca y su receta con ambos componentes.
        combo = _create_producto(
            client, admin_headers, nombre="Combo Papa + Coca", precio=6.0,
            tipo="compuesto", stock=50,
        )
        r = client.put(
            f"/productos/{combo['id']}/receta",
            json={
                "items": [
                    {"tipo": "producto", "componente_producto_id": papa["id"], "cantidad": 1},
                    {"tipo": "producto", "componente_producto_id": coca["id"], "cantidad": 1},
                ]
            },
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text

        # costo combo = papa(10×1) + coca(2) = 12
        # act + assert: el costeo del combo es 12.0.
        r = client.get("/costeo/productos", headers=admin_headers)
        fila = next(f for f in r.json() if f["producto_id"] == combo["id"])
        assert fila["costo"] == 12.0

        # act: vendemos 3 combos.
        r = client.post(
            "/ventas",
            json={"items": [{"producto_id": combo["id"], "cantidad": 3}], "pagos": []},
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text
        # assert: se descuentan los componentes (papa 100-3, coca 100-3) y el insumo.
        assert client.get(f"/productos/{papa['id']}", headers=admin_headers).json()["stock"] == 97
        assert client.get(f"/productos/{coca['id']}", headers=admin_headers).json()["stock"] == 97
        assert (
            client.get(f"/insumos/{papa_insumo['id']}", headers=admin_headers).json()["stock"]
            == 9970.0
        )

    def test_combo_ciclo_rechazado(self, client, admin_headers):
        """No se permite que dos combos se contengan mutuamente (ciclo)."""
        # arrange: dos productos compuestos A y B.
        a = _create_producto(client, admin_headers, nombre="A", tipo="compuesto", stock=10)
        b = _create_producto(client, admin_headers, nombre="B", tipo="compuesto", stock=10)
        # act: A usa a B dentro de su receta.
        client.put(
            f"/productos/{a['id']}/receta",
            json={"items": [{"tipo": "producto", "componente_producto_id": b["id"], "cantidad": 1}]},
            headers=admin_headers,
        )
        # act + assert: B no puede usar a A (crearía un ciclo) => 422.
        r = client.put(
            f"/productos/{b['id']}/receta",
            json={"items": [{"tipo": "producto", "componente_producto_id": a["id"], "cantidad": 1}]},
            headers=admin_headers,
        )
        assert r.status_code == 422

    def test_preparado_no_admite_producto(self, client, admin_headers):
        """Un producto preparado admite insumos, pero no otros productos."""
        # arrange: un insumo, un producto comprado y un producto preparado.
        insumo = _create_insumo(client, admin_headers)
        otro = _create_producto(client, admin_headers, nombre="Otro", tipo="comprado")
        precio = _create_producto(client, admin_headers, nombre="Prep", tipo="preparado")
        # act + assert: agregar un producto a un preparado falla (422).
        r = client.put(
            f"/productos/{precio['id']}/receta",
            json={"items": [{"tipo": "producto", "componente_producto_id": otro["id"], "cantidad": 1}]},
            headers=admin_headers,
        )
        assert r.status_code == 422
        # pero sí insumos
        # act + assert: en cambio, agregar un insumo al preparado sí funciona.
        r = client.put(
            f"/productos/{precio['id']}/receta",
            json={"items": [{"tipo": "insumo", "insumo_id": insumo["id"], "cantidad": 1}]},
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text
