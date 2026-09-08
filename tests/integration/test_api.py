def _create_producto(client, headers, nombre="Cafe", precio=2.0, stock=10):
    r = client.post(
        "/productos",
        json={"nombre": nombre, "precio": precio, "stock": stock},
        headers=headers,
    )
    assert r.status_code == 200
    return r.json()


class TestAuth:
    def test_login_correcto(self, client):
        r = client.post(
            "/auth/login",
            json={"email": "admin@cafeteriapos.com", "password": "admin123"},
        )
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_login_incorrecto(self, client):
        r = client.post(
            "/auth/login",
            json={"email": "admin@cafeteriapos.com", "password": "mal"},
        )
        assert r.status_code == 401

    def test_me(self, client, admin_headers):
        r = client.get("/auth/me", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["rol"] == "admin"

    def test_registro_requiere_admin(self, client, cajero_headers):
        r = client.post(
            "/auth/registro",
            json={
                "nombre": "X",
                "email": "x@x.com",
                "password": "password123",
                "rol": "cajero",
            },
            headers=cajero_headers,
        )
        assert r.status_code == 403

    def test_listar_usuarios_requiere_admin(self, client, cajero_headers):
        r = client.get("/auth/usuarios", headers=cajero_headers)
        assert r.status_code == 403

    def test_listar_usuarios(self, client, admin_headers):
        r = client.get("/auth/usuarios", headers=admin_headers)
        assert r.status_code == 200
        assert any(u["rol"] == "admin" for u in r.json())


class TestProductos:
    def test_crud(self, client, admin_headers):
        p = _create_producto(client, admin_headers)
        pid = p["id"]

        r = client.get("/productos", headers=admin_headers)
        assert r.status_code == 200
        assert len(r.json()) == 1

        r = client.get(f"/productos/{pid}", headers=admin_headers)
        assert r.json()["nombre"] == "Cafe"

        r = client.put(
            f"/productos/{pid}", json={"precio": 3.0}, headers=admin_headers
        )
        assert r.json()["precio"] == 3.0

        r = client.patch(
            f"/productos/{pid}/estado", json={"estado": False}, headers=admin_headers
        )
        assert r.json()["estado"] is False


class TestVentas:
    def test_crear_descuenta_stock_y_reporte(self, client, admin_headers):
        p = _create_producto(client, admin_headers, stock=10, precio=2.5)
        r = client.post(
            "/ventas",
            json={
                "items": [{"producto_id": p["id"], "cantidad": 3}],
                "pagos": [{"monto": 7.5, "metodo": "efectivo"}],
            },
            headers=admin_headers,
        )
        assert r.status_code == 200
        assert r.json()["total"] == 7.5
        assert r.json()["esta_pagada"] is True

        stock = client.get(f"/productos/{p['id']}", headers=admin_headers).json()["stock"]
        assert stock == 7

    def test_stock_insuficiente(self, client, admin_headers):
        p = _create_producto(client, admin_headers, stock=1)
        r = client.post(
            "/ventas",
            json={"items": [{"producto_id": p["id"], "cantidad": 5}], "pagos": []},
            headers=admin_headers,
        )
        assert r.status_code == 422

    def test_anular_reintegra_stock(self, client, admin_headers):
        p = _create_producto(client, admin_headers, stock=10)
        r = client.post(
            "/ventas",
            json={"items": [{"producto_id": p["id"], "cantidad": 2}], "pagos": []},
            headers=admin_headers,
        )
        venta_id = r.json()["id"]

        r = client.post(f"/ventas/{venta_id}/anular", headers=admin_headers)
        assert r.status_code == 200
        stock = client.get(f"/productos/{p['id']}", headers=admin_headers).json()["stock"]
        assert stock == 10

    def test_anular_requiere_admin(self, client, admin_headers, cajero_headers):
        p = _create_producto(client, admin_headers)
        r = client.post(
            "/ventas",
            json={"items": [{"producto_id": p["id"], "cantidad": 1}], "pagos": []},
            headers=cajero_headers,
        )
        venta_id = r.json()["id"]
        r = client.post(f"/ventas/{venta_id}/anular", headers=cajero_headers)
        assert r.status_code == 403

    def test_eliminar_reintegra_stock(self, client, admin_headers):
        p = _create_producto(client, admin_headers, stock=10)
        r = client.post(
            "/ventas",
            json={"items": [{"producto_id": p["id"], "cantidad": 4}], "pagos": []},
            headers=admin_headers,
        )
        venta_id = r.json()["id"]

        r = client.delete(f"/ventas/{venta_id}", headers=admin_headers)
        assert r.status_code == 200

        stock = client.get(f"/productos/{p['id']}", headers=admin_headers).json()["stock"]
        assert stock == 10

        r = client.get(f"/ventas/{venta_id}", headers=admin_headers)
        assert r.status_code == 404


class TestCompras:
    def test_crear_aumenta_stock(self, client, admin_headers):
        p = _create_producto(client, admin_headers, stock=2)
        r = client.post(
            "/compras",
            json={
                "proveedor_id": "prov1",
                "items": [{"producto_id": p["id"], "cantidad": 8, "precio_unitario": 1.0}],
            },
            headers=admin_headers,
        )
        assert r.status_code == 200
        assert r.json()["total"] == 8.0
        stock = client.get(f"/productos/{p['id']}", headers=admin_headers).json()["stock"]
        assert stock == 10

    def test_eliminar_compra(self, client, admin_headers):
        p = _create_producto(client, admin_headers, stock=2)
        r = client.post(
            "/compras",
            json={
                "proveedor_id": "prov1",
                "items": [{"producto_id": p["id"], "cantidad": 8, "precio_unitario": 1.0}],
            },
            headers=admin_headers,
        )
        compra_id = r.json()["id"]

        r = client.delete(f"/compras/{compra_id}", headers=admin_headers)
        assert r.status_code == 200

        stock = client.get(f"/productos/{p['id']}", headers=admin_headers).json()["stock"]
        assert stock == 2

        r = client.get(f"/compras/{compra_id}", headers=admin_headers)
        assert r.status_code == 404


class TestReportes:
    def test_resumen_y_top(self, client, admin_headers):
        p1 = _create_producto(client, admin_headers, nombre="Cafe", precio=2.0, stock=100)
        p2 = _create_producto(client, admin_headers, nombre="Te", precio=1.5, stock=100)

        client.post(
            "/ventas",
            json={
                "items": [{"producto_id": p1["id"], "cantidad": 4}],
                "pagos": [{"monto": 8.0, "metodo": "efectivo"}],
            },
            headers=admin_headers,
        )
        client.post(
            "/ventas",
            json={"items": [{"producto_id": p2["id"], "cantidad": 2}], "pagos": []},
            headers=admin_headers,
        )

        desde = "2000-01-01T00:00:00"
        hasta = "2100-01-01T00:00:00"

        r = client.get(
            f"/reportes/resumen?desde={desde}&hasta={hasta}", headers=admin_headers
        )
        assert r.status_code == 200
        assert r.json()["num_ventas"] == 2
        assert r.json()["total"] == 11.0

        r = client.get(
            f"/reportes/top-productos?desde={desde}&hasta={hasta}",
            headers=admin_headers,
        )
        assert r.status_code == 200
        top = r.json()
        assert top[0]["nombre"] == "Cafe"
        assert top[0]["cantidad"] == 4

    def test_ventas_por_periodo(self, client, admin_headers):
        p = _create_producto(client, admin_headers, stock=10)
        client.post(
            "/ventas",
            json={"items": [{"producto_id": p["id"], "cantidad": 1}], "pagos": []},
            headers=admin_headers,
        )
        desde = "2000-01-01T00:00:00"
        hasta = "2100-01-01T00:00:00"
        r = client.get(
            f"/reportes/ventas?desde={desde}&hasta={hasta}&agrupacion=dia",
            headers=admin_headers,
        )
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["num_ventas"] == 1


class TestSeguridad:
    def test_sin_token(self, client):
        assert client.get("/productos").status_code == 401
        assert client.get("/ventas").status_code == 401


class TestProveedores:
    def test_eliminar_sin_compras(self, client, admin_headers):
        r = client.post(
            "/proveedores",
            json={"nombre": "Acme", "contacto": "Juan", "telefono": "123"},
            headers=admin_headers,
        )
        pid = r.json()["id"]

        r = client.delete(f"/proveedores/{pid}", headers=admin_headers)
        assert r.status_code == 200

        r = client.get(f"/proveedores/{pid}", headers=admin_headers)
        assert r.status_code == 404

    def test_eliminar_con_compras(self, client, admin_headers):
        r = client.post(
            "/proveedores",
            json={"nombre": "Acme", "contacto": "Juan", "telefono": "123"},
            headers=admin_headers,
        )
        pid = r.json()["id"]

        p = _create_producto(client, admin_headers)
        client.post(
            "/compras",
            json={
                "proveedor_id": pid,
                "items": [{"producto_id": p["id"], "cantidad": 5, "precio_unitario": 1.0}],
            },
            headers=admin_headers,
        )

        r = client.delete(f"/proveedores/{pid}", headers=admin_headers)
        assert r.status_code == 409


class TestConfiguracion:
    def test_obtener_publico(self, client):
        r = client.get("/configuracion")
        assert r.status_code == 200

    def test_actualizar_logo_requiere_admin(self, client, cajero_headers):
        r = client.put(
            "/configuracion/logo",
            json={"logo": "data:image/png;base64,AAAA"},
            headers=cajero_headers,
        )
        assert r.status_code == 403

    def test_actualizar_y_obtener_logo(self, client, admin_headers):
        r = client.put(
            "/configuracion/logo",
            json={"logo": "data:image/png;base64,AAAA"},
            headers=admin_headers,
        )
        assert r.status_code == 200

        r = client.get("/configuracion")
        assert r.json()["logo"] == "data:image/png;base64,AAAA"


class TestPermisosCajero:
    def test_no_crea_productos(self, client, admin_headers, cajero_headers):
        r = client.post(
            "/productos", json={"nombre": "X", "precio": 1, "stock": 1}, headers=cajero_headers
        )
        assert r.status_code == 403

    def test_no_edita_estado_producto(self, client, admin_headers, cajero_headers):
        p = _create_producto(client, admin_headers)
        r = client.patch(
            f"/productos/{p['id']}/estado", json={"estado": False}, headers=cajero_headers
        )
        assert r.status_code == 403

    def test_no_crea_categorias(self, client, cajero_headers):
        r = client.post("/categorias", json={"nombre": "X"}, headers=cajero_headers)
        assert r.status_code == 403

    def test_no_crea_proveedores(self, client, cajero_headers):
        r = client.post(
            "/proveedores",
            json={"nombre": "A", "contacto": "C", "telefono": "T"},
            headers=cajero_headers,
        )
        assert r.status_code == 403

    def test_no_edita_proveedor(self, client, admin_headers, cajero_headers):
        r = client.post(
            "/proveedores",
            json={"nombre": "A", "contacto": "C", "telefono": "T"},
            headers=admin_headers,
        )
        pid = r.json()["id"]
        r = client.put(
            f"/proveedores/{pid}", json={"nombre": "B"}, headers=cajero_headers
        )
        assert r.status_code == 403

    def test_no_genera_reportes(self, client, cajero_headers):
        r = client.get(
            "/reportes/ventas?desde=2000-01-01T00:00:00&hasta=2100-01-01T00:00:00&agrupacion=dia",
            headers=cajero_headers,
        )
        assert r.status_code == 403

    def test_si_crea_venta(self, client, admin_headers, cajero_headers):
        p = _create_producto(client, admin_headers)
        r = client.post(
            "/ventas",
            json={"items": [{"producto_id": p["id"], "cantidad": 1}], "pagos": []},
            headers=cajero_headers,
        )
        assert r.status_code == 200
