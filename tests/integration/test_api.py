"""Pruebas de integración de la API HTTP (endpoints reales con TestClient).

A diferencia de las pruebas unitarias, aquí arrancamos la aplicación FastAPI
completa contra una base de datos SQLite temporal. El fixture `client`
(definido en tests/conftest.py) simula peticiones HTTP reales, y los fixtures
`admin_headers` / `cajero_headers` aportan los tokens JWT de cada rol.

Se verifican rutas, códigos de estado HTTP, permisos por rol y los efectos en
los datos (por ejemplo, que una venta descuente stock). Cada prueba sigue el
patrón arrange (preparar), act (ejecutar) y assert (comprobar).
"""


def _create_producto(client, headers, nombre="Cafe", precio=2.0, stock=10):
    """Helper: crea un producto vía API y devuelve su JSON.

    Se reutiliza en muchas pruebas para tener un producto listo. Falla si la
    API no responde 200.
    """
    r = client.post(
        "/productos",
        json={"nombre": nombre, "precio": precio, "stock": stock},
        headers=headers,
    )
    # assert: la creación debe ser exitosa.
    assert r.status_code == 200
    return r.json()


class TestAuth:
    """Prueba el login, el usuario actual y la administración de usuarios."""

    def test_login_correcto(self, client):
        """Un login con credenciales válidas devuelve un access_token."""
        # act: iniciamos sesión con el admin sembrado.
        r = client.post(
            "/auth/login",
            json={"email": "admin@cafeteriapos.com", "password": "admin123"},
        )
        # assert: responde 200 y entrega el token.
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_login_incorrecto(self, client):
        """Un login con contraseña errónea devuelve 401 (no autorizado)."""
        # act: intentamos entrar con una contraseña mala.
        r = client.post(
            "/auth/login",
            json={"email": "admin@cafeteriapos.com", "password": "mal"},
        )
        # assert: la API rechaza con 401.
        assert r.status_code == 401

    def test_me(self, client, admin_headers):
        """El endpoint /auth/me devuelve los datos del usuario autenticado."""
        # act: consultamos el "yo" con el token del admin.
        r = client.get("/auth/me", headers=admin_headers)
        # assert: responde 200 y el rol es admin.
        assert r.status_code == 200
        assert r.json()["rol"] == "admin"

    def test_registro_requiere_admin(self, client, cajero_headers):
        """Un cajero no puede registrar usuarios (403)."""
        # act: el cajero intenta registrar a otro usuario.
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
        # assert: la API lo prohíbe con 403.
        assert r.status_code == 403

    def test_listar_usuarios_requiere_admin(self, client, cajero_headers):
        """Un cajero no puede listar usuarios (403)."""
        # act: el cajero intenta listar usuarios.
        r = client.get("/auth/usuarios", headers=cajero_headers)
        # assert: prohibido para cajero.
        assert r.status_code == 403

    def test_listar_usuarios(self, client, admin_headers):
        """El admin sí puede listar usuarios y aparece al menos un admin."""
        # act: listamos usuarios con el token del admin.
        r = client.get("/auth/usuarios", headers=admin_headers)
        # assert: responde 200 y hay un usuario con rol admin.
        assert r.status_code == 200
        assert any(u["rol"] == "admin" for u in r.json())


class TestProductos:
    """Prueba el CRUD básico de productos."""

    def test_crud(self, client, admin_headers):
        """Crea, lista, consulta, edita precio y cambia el estado de un producto."""
        # arrange: creamos un producto por API.
        p = _create_producto(client, admin_headers)
        pid = p["id"]

        # act + assert: lo listamos y debe haber exactamente uno.
        r = client.get("/productos", headers=admin_headers)
        assert r.status_code == 200
        assert len(r.json()) == 1

        # act + assert: lo consultamos por id y el nombre coincide.
        r = client.get(f"/productos/{pid}", headers=admin_headers)
        assert r.json()["nombre"] == "Cafe"

        # act + assert: editamos el precio a 3.0.
        r = client.put(
            f"/productos/{pid}", json={"precio": 3.0}, headers=admin_headers
        )
        assert r.json()["precio"] == 3.0

        # act + assert: lo desactivamos.
        r = client.patch(
            f"/productos/{pid}/estado", json={"estado": False}, headers=admin_headers
        )
        assert r.json()["estado"] is False


class TestVentas:
    """Prueba la creación, anulación y eliminación de ventas y su efecto en stock."""

    def test_crear_descuenta_stock_y_reporte(self, client, admin_headers):
        """Crear una venta descuenta stock y la deja pagada si el pago alcanza."""
        # arrange: producto con 10 unidades a 2.5.
        p = _create_producto(client, admin_headers, stock=10, precio=2.5)
        # act: vendemos 3 unidades pagando 7.5 (el total exacto).
        r = client.post(
            "/ventas",
            json={
                "items": [{"producto_id": p["id"], "cantidad": 3}],
                "pagos": [{"monto": 7.5, "metodo": "efectivo"}],
            },
            headers=admin_headers,
        )
        # assert: total 3×2.5=7.5 y la venta queda pagada.
        assert r.status_code == 200
        assert r.json()["total"] == 7.5
        assert r.json()["esta_pagada"] is True

        # assert: el stock bajó de 10 a 7.
        stock = client.get(f"/productos/{p['id']}", headers=admin_headers).json()["stock"]
        assert stock == 7

    def test_stock_insuficiente(self, client, admin_headers):
        """Vender más de lo disponible devuelve 422 (error de validación)."""
        # arrange: producto con una sola unidad.
        p = _create_producto(client, admin_headers, stock=1)
        # act: intentamos vender 5.
        r = client.post(
            "/ventas",
            json={"items": [{"producto_id": p["id"], "cantidad": 5}], "pagos": []},
            headers=admin_headers,
        )
        # assert: la API responde 422.
        assert r.status_code == 422

    def test_anular_reintegra_stock(self, client, admin_headers):
        """Anular una venta devuelve las unidades al stock."""
        # arrange: producto con 10 unidades y venta de 2.
        p = _create_producto(client, admin_headers, stock=10)
        r = client.post(
            "/ventas",
            json={"items": [{"producto_id": p["id"], "cantidad": 2}], "pagos": []},
            headers=admin_headers,
        )
        venta_id = r.json()["id"]

        # act: anulamos la venta.
        r = client.post(f"/ventas/{venta_id}/anular", headers=admin_headers)
        # assert: responde 200 y el stock vuelve a 10.
        assert r.status_code == 200
        stock = client.get(f"/productos/{p['id']}", headers=admin_headers).json()["stock"]
        assert stock == 10

    def test_anular_requiere_admin(self, client, admin_headers, cajero_headers):
        """Un cajero puede crear ventas pero no anularlas (403)."""
        # arrange: el admin crea un producto y el cajero registra una venta.
        p = _create_producto(client, admin_headers)
        r = client.post(
            "/ventas",
            json={"items": [{"producto_id": p["id"], "cantidad": 1}], "pagos": []},
            headers=cajero_headers,
        )
        venta_id = r.json()["id"]
        # act: el cajero intenta anularla.
        r = client.post(f"/ventas/{venta_id}/anular", headers=cajero_headers)
        # assert: prohibido para cajero.
        assert r.status_code == 403

    def test_eliminar_reintegra_stock(self, client, admin_headers):
        """Eliminar una venta reintegra el stock y luego ya no se encuentra."""
        # arrange: producto con 10 unidades y venta de 4.
        p = _create_producto(client, admin_headers, stock=10)
        r = client.post(
            "/ventas",
            json={"items": [{"producto_id": p["id"], "cantidad": 4}], "pagos": []},
            headers=admin_headers,
        )
        venta_id = r.json()["id"]

        # act: eliminamos la venta.
        r = client.delete(f"/ventas/{venta_id}", headers=admin_headers)
        # assert: responde 200.
        assert r.status_code == 200

        # assert: el stock vuelve a 10.
        stock = client.get(f"/productos/{p['id']}", headers=admin_headers).json()["stock"]
        assert stock == 10

        # assert: la venta eliminada ya no existe (404).
        r = client.get(f"/ventas/{venta_id}", headers=admin_headers)
        assert r.status_code == 404


class TestCompras:
    """Prueba la creación y eliminación de compras y su efecto en stock."""

    def test_crear_aumenta_stock(self, client, admin_headers):
        """Registrar una compra aumenta el stock del producto."""
        # arrange: producto con 2 unidades.
        p = _create_producto(client, admin_headers, stock=2)
        # act: compramos 8 unidades a 1.0.
        r = client.post(
            "/compras",
            json={
                "proveedor_id": "prov1",
                "items": [{"producto_id": p["id"], "cantidad": 8, "precio_unitario": 1.0}],
            },
            headers=admin_headers,
        )
        # assert: total 8.0 y stock 2+8=10.
        assert r.status_code == 200
        assert r.json()["total"] == 8.0
        stock = client.get(f"/productos/{p['id']}", headers=admin_headers).json()["stock"]
        assert stock == 10

    def test_eliminar_compra(self, client, admin_headers):
        """Eliminar una compra resta del stock lo que había sumado."""
        # arrange: producto con 2 unidades y compra de 8.
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

        # act: eliminamos la compra.
        r = client.delete(f"/compras/{compra_id}", headers=admin_headers)
        # assert: responde 200 y el stock vuelve a 2.
        assert r.status_code == 200

        stock = client.get(f"/productos/{p['id']}", headers=admin_headers).json()["stock"]
        assert stock == 2

        # assert: la compra eliminada ya no existe (404).
        r = client.get(f"/compras/{compra_id}", headers=admin_headers)
        assert r.status_code == 404


class TestReportes:
    """Prueba los reportes: resumen, top de productos, ventas y actividad."""

    def test_resumen_y_top(self, client, admin_headers):
        """El resumen suma ventas y el top ordena por cantidad vendida."""
        # arrange: dos productos y dos ventas.
        p1 = _create_producto(client, admin_headers, nombre="Cafe", precio=2.0, stock=100)
        p2 = _create_producto(client, admin_headers, nombre="Te", precio=1.5, stock=100)

        # act: vendemos 4 cafés (8.0) y 2 tés sin pagar.
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

        # Rango de fechas amplio para incluir las ventas recién creadas.
        desde = "2000-01-01T00:00:00"
        hasta = "2100-01-01T00:00:00"

        # act + assert: el resumen cuenta 2 ventas y total 8.0 + 3.0 = 11.0.
        r = client.get(
            f"/reportes/resumen?desde={desde}&hasta={hasta}", headers=admin_headers
        )
        assert r.status_code == 200
        assert r.json()["num_ventas"] == 2
        assert r.json()["total"] == 11.0

        # act + assert: el top pone primero al "Cafe" con 4 unidades.
        r = client.get(
            f"/reportes/top-productos?desde={desde}&hasta={hasta}",
            headers=admin_headers,
        )
        assert r.status_code == 200
        top = r.json()
        assert top[0]["nombre"] == "Cafe"
        assert top[0]["cantidad"] == 4

    def test_ventas_por_periodo(self, client, admin_headers):
        """El reporte de ventas por día agrupa las ventas del período."""
        # arrange: producto y una venta.
        p = _create_producto(client, admin_headers, stock=10)
        client.post(
            "/ventas",
            json={"items": [{"producto_id": p["id"], "cantidad": 1}], "pagos": []},
            headers=admin_headers,
        )
        desde = "2000-01-01T00:00:00"
        hasta = "2100-01-01T00:00:00"
        # act: pedimos el reporte agrupado por día.
        r = client.get(
            f"/reportes/ventas?desde={desde}&hasta={hasta}&agrupacion=dia",
            headers=admin_headers,
        )
        # assert: hay un grupo y contiene 1 venta.
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["num_ventas"] == 1

    def test_actividad_por_hora(self, client, admin_headers, cajero_headers):
        """El reporte de actividad por hora puede consultarlo un cajero."""
        # arrange: el admin crea producto y venta.
        p = _create_producto(client, admin_headers, stock=10)
        client.post(
            "/ventas",
            json={"items": [{"producto_id": p["id"], "cantidad": 1}], "pagos": []},
            headers=admin_headers,
        )
        desde = "2000-01-01T00:00:00"
        hasta = "2100-01-01T00:00:00"
        # act: el cajero consulta la actividad agrupada por hora.
        r = client.get(
            f"/reportes/actividad?desde={desde}&hasta={hasta}&agrupacion=hora",
            headers=cajero_headers,
        )
        # assert: responde 200 y hay un grupo con 1 venta.
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["num_ventas"] == 1

    def test_actividad_agrupacion_invalida(self, client, admin_headers):
        """Una agrupación desconocida devuelve 422 (validación)."""
        # act: pedimos actividad con agrupacion="foo".
        r = client.get(
            "/reportes/actividad?desde=2000-01-01T00:00:00"
            "&hasta=2100-01-01T00:00:00&agrupacion=foo",
            headers=admin_headers,
        )
        # assert: la API responde 422.
        assert r.status_code == 422


class TestSeguridad:
    """Prueba que los endpoints protegidos exigen autenticación."""

    def test_sin_token(self, client):
        """Sin token, los recursos protegidos devuelven 401."""
        # assert: tanto productos como ventas exigen token.
        assert client.get("/productos").status_code == 401
        assert client.get("/ventas").status_code == 401


class TestProveedores:
    """Prueba la eliminación de proveedores según tengan compras o no."""

    def test_eliminar_sin_compras(self, client, admin_headers):
        """Un proveedor sin compras se puede eliminar."""
        # arrange: creamos un proveedor.
        r = client.post(
            "/proveedores",
            json={"nombre": "Acme", "contacto": "Juan", "telefono": "123"},
            headers=admin_headers,
        )
        pid = r.json()["id"]

        # act: lo eliminamos.
        r = client.delete(f"/proveedores/{pid}", headers=admin_headers)
        # assert: responde 200 y luego ya no existe (404).
        assert r.status_code == 200

        r = client.get(f"/proveedores/{pid}", headers=admin_headers)
        assert r.status_code == 404

    def test_eliminar_con_compras(self, client, admin_headers):
        """Un proveedor con compras no se puede eliminar (409 conflicto)."""
        # arrange: creamos proveedor, producto y una compra de ese proveedor.
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

        # act: intentamos eliminar el proveedor.
        r = client.delete(f"/proveedores/{pid}", headers=admin_headers)
        # assert: la API rechaza con 409 por tener compras asociadas.
        assert r.status_code == 409


class TestConfiguracion:
    """Prueba la lectura pública y la actualización protegida de la configuración."""

    def test_obtener_publico(self, client):
        """La configuración se puede leer sin token (es pública)."""
        # act + assert: sin cabeceras responde 200.
        r = client.get("/configuracion")
        assert r.status_code == 200

    def test_actualizar_logo_requiere_admin(self, client, cajero_headers):
        """Actualizar el logo requiere ser admin (403 para cajero)."""
        # act: el cajero intenta actualizar el logo.
        r = client.put(
            "/configuracion/logo",
            json={"logo": "data:image/png;base64,AAAA"},
            headers=cajero_headers,
        )
        # assert: prohibido para cajero.
        assert r.status_code == 403

    def test_actualizar_y_obtener_logo(self, client, admin_headers):
        """El admin puede actualizar el logo y luego se lee actualizado."""
        # act: el admin actualiza el logo.
        r = client.put(
            "/configuracion/logo",
            json={"logo": "data:image/png;base64,AAAA"},
            headers=admin_headers,
        )
        # assert: responde 200.
        assert r.status_code == 200

        # assert: al leer la configuración, el logo es el nuevo.
        r = client.get("/configuracion")
        assert r.json()["logo"] == "data:image/png;base64,AAAA"


class TestPermisosCajero:
    """Prueba que un cajero no puede administrar catálogos, pero sí vender."""

    def test_no_crea_productos(self, client, admin_headers, cajero_headers):
        """Un cajero no puede crear productos (403)."""
        # act: el cajero intenta crear un producto.
        r = client.post(
            "/productos", json={"nombre": "X", "precio": 1, "stock": 1}, headers=cajero_headers
        )
        # assert: prohibido.
        assert r.status_code == 403

    def test_no_edita_estado_producto(self, client, admin_headers, cajero_headers):
        """Un cajero no puede activar/desactivar un producto (403)."""
        # arrange: el admin crea el producto.
        p = _create_producto(client, admin_headers)
        # act: el cajero intenta cambiar el estado.
        r = client.patch(
            f"/productos/{p['id']}/estado", json={"estado": False}, headers=cajero_headers
        )
        # assert: prohibido.
        assert r.status_code == 403

    def test_no_crea_categorias(self, client, cajero_headers):
        """Un cajero no puede crear categorías (403)."""
        # act + assert: la creación de categorías está prohibida para cajero.
        r = client.post("/categorias", json={"nombre": "X"}, headers=cajero_headers)
        assert r.status_code == 403

    def test_no_crea_proveedores(self, client, cajero_headers):
        """Un cajero no puede crear proveedores (403)."""
        # act + assert: prohibido crear proveedores como cajero.
        r = client.post(
            "/proveedores",
            json={"nombre": "A", "contacto": "C", "telefono": "T"},
            headers=cajero_headers,
        )
        assert r.status_code == 403

    def test_no_edita_proveedor(self, client, admin_headers, cajero_headers):
        """Un cajero no puede editar proveedores (403)."""
        # arrange: el admin crea un proveedor.
        r = client.post(
            "/proveedores",
            json={"nombre": "A", "contacto": "C", "telefono": "T"},
            headers=admin_headers,
        )
        pid = r.json()["id"]
        # act: el cajero intenta editarlo.
        r = client.put(
            f"/proveedores/{pid}", json={"nombre": "B"}, headers=cajero_headers
        )
        # assert: prohibido.
        assert r.status_code == 403

    def test_no_genera_reportes(self, client, cajero_headers):
        """Un cajero no puede generar el reporte de ventas (403)."""
        # act + assert: pedir reportes de ventas está prohibido para cajero.
        r = client.get(
            "/reportes/ventas?desde=2000-01-01T00:00:00&hasta=2100-01-01T00:00:00&agrupacion=dia",
            headers=cajero_headers,
        )
        assert r.status_code == 403

    def test_si_crea_venta(self, client, admin_headers, cajero_headers):
        """Un cajero SÍ puede registrar una venta."""
        # arrange: el admin crea el producto.
        p = _create_producto(client, admin_headers)
        # act: el cajero vende 1 unidad.
        r = client.post(
            "/ventas",
            json={"items": [{"producto_id": p["id"], "cantidad": 1}], "pagos": []},
            headers=cajero_headers,
        )
        # assert: la venta se crea correctamente (200).
        assert r.status_code == 200
