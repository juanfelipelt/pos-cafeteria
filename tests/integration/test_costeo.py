from datetime import datetime, timedelta


def _rango_hoy():
    ahora = datetime.now()
    desde = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    hasta = desde + timedelta(days=1) - timedelta(microseconds=1)
    return desde.isoformat(), hasta.isoformat()


def _create_insumo(client, headers, nombre="Cafe", unidad="g", stock=0.0, costo=0.0):
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
    assert r.status_code == 200, r.text
    return r.json()


def _create_producto(
    client, headers, nombre="Capuchino", precio=5.0, tipo="preparado", stock=0
):
    r = client.post(
        "/productos",
        json={"nombre": nombre, "precio": precio, "stock": stock, "tipo": tipo},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    return r.json()


class TestInsumos:
    def test_crud(self, client, admin_headers):
        insumo = _create_insumo(client, admin_headers, stock=100, costo=2.0)
        assert insumo["nombre"] == "Cafe"
        assert insumo["unidad"] == "g"

        r = client.get("/insumos", headers=admin_headers)
        assert r.status_code == 200
        assert len(r.json()) == 1

        r = client.put(
            f"/insumos/{insumo['id']}",
            json={"costo_unitario": 3.0},
            headers=admin_headers,
        )
        assert r.json()["costo_unitario"] == 3.0

        r = client.patch(
            f"/insumos/{insumo['id']}/estado",
            json={"estado": False},
            headers=admin_headers,
        )
        assert r.json()["estado"] is False

        r = client.delete(f"/insumos/{insumo['id']}", headers=admin_headers)
        assert r.status_code == 200

    def test_crear_requiere_admin(self, client, cajero_headers):
        r = client.post(
            "/insumos",
            json={"nombre": "X", "unidad": "g"},
            headers=cajero_headers,
        )
        assert r.status_code == 403

    def test_nombre_y_unidad_obligatorios(self, client, admin_headers):
        r = client.post(
            "/insumos", json={"nombre": "", "unidad": "g"}, headers=admin_headers
        )
        assert r.status_code == 422


class TestReceta:
    def test_receta_calcula_costo(self, client, admin_headers):
        insumo = _create_insumo(client, admin_headers, stock=1000, costo=2.0)
        producto = _create_producto(client, admin_headers)

        r = client.put(
            f"/productos/{producto['id']}/receta",
            json={"items": [{"insumo_id": insumo["id"], "cantidad": 10}]},
            headers=admin_headers,
        )
        assert r.status_code == 200
        assert r.json()[0]["subtotal"] == 20.0

        r = client.get("/costeo/productos", headers=admin_headers)
        assert r.status_code == 200
        fila = next(f for f in r.json() if f["producto_id"] == producto["id"])
        assert fila["costo"] == 20.0
        assert fila["margen"] == producto["precio"] - 20.0

    def test_receta_solo_preparado(self, client, admin_headers):
        insumo = _create_insumo(client, admin_headers)
        producto = _create_producto(
            client, admin_headers, nombre="Gaseosa", tipo="comprado"
        )
        r = client.put(
            f"/productos/{producto['id']}/receta",
            json={"items": [{"insumo_id": insumo["id"], "cantidad": 1}]},
            headers=admin_headers,
        )
        assert r.status_code == 422


class TestCompraInsumo:
    def _proveedor(self, client, headers):
        return client.post(
            "/proveedores",
            json={"nombre": "Prov", "contacto": "X", "telefono": "1"},
            headers=headers,
        ).json()

    def test_promedio_ponderado(self, client, admin_headers):
        prov = self._proveedor(client, admin_headers)
        insumo = _create_insumo(client, admin_headers, stock=100, costo=2.0)

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

        r = client.get(f"/insumos/{insumo['id']}", headers=admin_headers)
        assert r.json()["stock"] == 200
        assert r.json()["costo_unitario"] == 3.0

    def test_editar_compra_ajusta_stock_y_costo(self, client, admin_headers):
        prov = self._proveedor(client, admin_headers)
        insumo = _create_insumo(
            client, admin_headers, stock=0, costo=0
        )
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

        ins = client.get(f"/insumos/{insumo['id']}", headers=admin_headers).json()
        assert ins["stock"] == 200
        # (100×2 + 100×10) / 200 = 6.0
        assert ins["costo_unitario"] == 6.0

    def test_editar_compra_requiere_admin(self, client, admin_headers, cajero_headers):
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
        assert r.status_code == 403

    def test_editar_compra_anulada(self, client, admin_headers):
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
        assert r.status_code == 422


class TestCostosFijos:
    def test_crud(self, client, admin_headers):
        r = client.post(
            "/costos-fijos",
            json={"nombre": "Arriendo", "monto": 1000000},
            headers=admin_headers,
        )
        assert r.status_code == 200
        costo = r.json()

        r = client.get("/costos-fijos", headers=admin_headers)
        assert len(r.json()) == 1

        r = client.put(
            f"/costos-fijos/{costo['id']}",
            json={"monto": 1200000},
            headers=admin_headers,
        )
        assert r.json()["monto"] == 1200000

        r = client.delete(f"/costos-fijos/{costo['id']}", headers=admin_headers)
        assert r.status_code == 200


class TestCosteoResumen:
    def test_resumen_con_venta(self, client, admin_headers):
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
        r = client.post(
            "/ventas",
            json={"items": [{"producto_id": producto["id"], "cantidad": 3}], "pagos": []},
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text

        desde, hasta = _rango_hoy()
        r = client.get(
            f"/costeo/resumen?desde={desde}&hasta={hasta}",
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["ventas"] == 15.0
        assert data["costo_variable"] == 6.0
        assert data["margen"] == 9.0
        assert data["costos_fijos_mes"] == 260000
        assert data["dias_laborables_mes"] > 0
        assert data["punto_equilibrio"] is not None

    def test_resumen_requiere_admin(self, client, cajero_headers):
        desde, hasta = _rango_hoy()
        r = client.get(
            f"/costeo/resumen?desde={desde}&hasta={hasta}",
            headers=cajero_headers,
        )
        assert r.status_code == 403

    def test_resumen_prorratea_mes(self, client, admin_headers):
        client.post(
            "/costos-fijos",
            json={"nombre": "Arriendo", "monto": 260000},
            headers=admin_headers,
        )
        r = client.get(
            "/costeo/resumen?desde=2024-06-01T00:00:00"
            "&hasta=2024-07-05T23:59:59",
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["costos_fijos_mes"] == 260000
        assert 260000 <= data["costo_fijo_periodo"] <= 520000

    def test_venta_guarda_costo_y_descuenta_insumo(self, client, admin_headers):
        insumo = _create_insumo(client, admin_headers, stock=1000, costo=1.0)
        producto = _create_producto(client, admin_headers, precio=5.0, stock=10)
        client.put(
            f"/productos/{producto['id']}/receta",
            json={"items": [{"insumo_id": insumo["id"], "cantidad": 2}]},
            headers=admin_headers,
        )
        r = client.post(
            "/ventas",
            json={"items": [{"producto_id": producto["id"], "cantidad": 3}], "pagos": []},
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text
        venta = r.json()
        assert venta["detalles"][0]["costo_unitario"] == 2.0

        r = client.get(f"/insumos/{insumo['id']}", headers=admin_headers)
        assert r.json()["stock"] == 994.0  # 1000 - 2*3


class TestProductoCompuesto:
    def _proveedor(self, client, headers):
        return client.post(
            "/proveedores",
            json={"nombre": "Prov", "contacto": "X", "telefono": "1"},
            headers=headers,
        ).json()

    def test_combo_costo_y_consumo(self, client, admin_headers):
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
        r = client.get("/costeo/productos", headers=admin_headers)
        fila = next(f for f in r.json() if f["producto_id"] == combo["id"])
        assert fila["costo"] == 12.0

        r = client.post(
            "/ventas",
            json={"items": [{"producto_id": combo["id"], "cantidad": 3}], "pagos": []},
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text
        assert client.get(f"/productos/{papa['id']}", headers=admin_headers).json()["stock"] == 97
        assert client.get(f"/productos/{coca['id']}", headers=admin_headers).json()["stock"] == 97
        assert (
            client.get(f"/insumos/{papa_insumo['id']}", headers=admin_headers).json()["stock"]
            == 9970.0
        )

    def test_combo_ciclo_rechazado(self, client, admin_headers):
        a = _create_producto(client, admin_headers, nombre="A", tipo="compuesto", stock=10)
        b = _create_producto(client, admin_headers, nombre="B", tipo="compuesto", stock=10)
        client.put(
            f"/productos/{a['id']}/receta",
            json={"items": [{"tipo": "producto", "componente_producto_id": b["id"], "cantidad": 1}]},
            headers=admin_headers,
        )
        r = client.put(
            f"/productos/{b['id']}/receta",
            json={"items": [{"tipo": "producto", "componente_producto_id": a["id"], "cantidad": 1}]},
            headers=admin_headers,
        )
        assert r.status_code == 422

    def test_preparado_no_admite_producto(self, client, admin_headers):
        insumo = _create_insumo(client, admin_headers)
        otro = _create_producto(client, admin_headers, nombre="Otro", tipo="comprado")
        precio = _create_producto(client, admin_headers, nombre="Prep", tipo="preparado")
        r = client.put(
            f"/productos/{precio['id']}/receta",
            json={"items": [{"tipo": "producto", "componente_producto_id": otro["id"], "cantidad": 1}]},
            headers=admin_headers,
        )
        assert r.status_code == 422
        # pero sí insumos
        r = client.put(
            f"/productos/{precio['id']}/receta",
            json={"items": [{"tipo": "insumo", "insumo_id": insumo["id"], "cantidad": 1}]},
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text
