class TestNotas:
    def test_crud_y_permisos(self, client, admin_headers, cajero_headers):
        r = client.post(
            "/notas",
            json={
                "texto": "Reponer azúcar",
                "tipo": "tarea",
                "destinatario": "cajero",
                "prioridad": "alta",
            },
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text
        nota = r.json()
        assert nota["tipo"] == "tarea"
        assert nota["autor_nombre"] == "Administrador"

        r = client.get("/notas", headers=cajero_headers)
        assert len(r.json()) == 1

        # La cajera puede marcar hecha
        r = client.patch(
            f"/notas/{nota['id']}", json={"hecho": True}, headers=cajero_headers
        )
        assert r.status_code == 200
        assert r.json()["hecho"] is True

        # Pero no editar el texto (no es autora ni admin)
        r = client.patch(
            f"/notas/{nota['id']}", json={"texto": "otra"}, headers=cajero_headers
        )
        assert r.status_code == 403

        # Ni eliminar
        r = client.delete(f"/notas/{nota['id']}", headers=cajero_headers)
        assert r.status_code == 403

        # El admin sí
        r = client.delete(f"/notas/{nota['id']}", headers=admin_headers)
        assert r.status_code == 200

    def test_autor_edita_y_archiva(self, client, admin_headers, cajero_headers):
        r = client.post(
            "/notas",
            json={"texto": "Se acabó el café", "destinatario": "admin", "prioridad": "alta"},
            headers=cajero_headers,
        )
        nota = r.json()
        assert nota["autor_nombre"] == "Cajero"

        r = client.patch(
            f"/notas/{nota['id']}",
            json={"texto": "Se acabó el café molido", "archivada": True},
            headers=cajero_headers,
        )
        assert r.status_code == 200
        assert r.json()["archivada"] is True

    def test_filtros_y_resumen(self, client, admin_headers):
        client.post("/notas", json={"texto": "t1", "tipo": "tarea"}, headers=admin_headers)
        t2 = client.post(
            "/notas", json={"texto": "t2", "tipo": "tarea"}, headers=admin_headers
        ).json()
        client.post("/notas", json={"texto": "n1", "tipo": "nota"}, headers=admin_headers)

        r = client.get("/notas?tipo=tarea", headers=admin_headers)
        assert len(r.json()) == 2

        r = client.get("/notas/resumen", headers=admin_headers)
        data = r.json()
        assert data["tareas_pendientes"] == 2
        assert data["notas"] == 1
        assert data["pendientes"] == 3

        # Marcar una hecha y archivar una nota
        client.patch(f"/notas/{t2['id']}", json={"hecho": True}, headers=admin_headers)
        r = client.get("/notas/resumen", headers=admin_headers)
        assert r.json()["tareas_pendientes"] == 1

    def test_filtro_destinatario_incluye_todos(self, client, admin_headers):
        client.post(
            "/notas", json={"texto": "global", "destinatario": "todos"}, headers=admin_headers
        )
        client.post(
            "/notas", json={"texto": "solo admin", "destinatario": "admin"}, headers=admin_headers
        )
        r = client.get("/notas?destinatario=admin", headers=admin_headers)
        # incluye la de admin y la de todos
        assert len(r.json()) == 2
        r = client.get("/notas?destinatario=cajero", headers=admin_headers)
        # solo la de todos
        assert len(r.json()) == 1

    def test_texto_obligatorio(self, client, admin_headers):
        r = client.post("/notas", json={"texto": "   "}, headers=admin_headers)
        assert r.status_code == 422
