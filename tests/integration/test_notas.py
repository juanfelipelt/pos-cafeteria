"""Pruebas de integración de las NOTAS (pizarra de tareas y avisos).

Estas pruebas verifican, a través de la API real, el ciclo de vida de las notas:
crearlas, listarlas con filtros, marcarlas como hechas, editarlas, archivarlas
y eliminarlas, además de las reglas de permisos según quién sea el autor.

Cada prueba sigue el patrón arrange (preparar), act (ejecutar) y assert
(comprobar).
"""


class TestNotas:
    """Prueba el CRUD de notas, sus filtros, el resumen y los permisos."""

    def test_crud_y_permisos(self, client, admin_headers, cajero_headers):
        """Crea una nota y comprueba quién puede verla, marcarla, editarla y borrarla."""
        # arrange/act: el admin crea una tarea dirigida a la cajera.
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
        # assert: se crea correctamente y registra a su autor.
        assert r.status_code == 200, r.text
        nota = r.json()
        assert nota["tipo"] == "tarea"
        assert nota["autor_nombre"] == "Administrador"

        # act + assert: la cajera puede listar las notas (hay 1).
        r = client.get("/notas", headers=cajero_headers)
        assert len(r.json()) == 1

        # La cajera puede marcar hecha
        # act + assert: la destinataria puede marcarla como hecha.
        r = client.patch(
            f"/notas/{nota['id']}", json={"hecho": True}, headers=cajero_headers
        )
        assert r.status_code == 200
        assert r.json()["hecho"] is True

        # Pero no editar el texto (no es autora ni admin)
        # act + assert: la cajera no puede cambiar el texto (403).
        r = client.patch(
            f"/notas/{nota['id']}", json={"texto": "otra"}, headers=cajero_headers
        )
        assert r.status_code == 403

        # Ni eliminar
        # act + assert: la cajera tampoco puede eliminarla (403).
        r = client.delete(f"/notas/{nota['id']}", headers=cajero_headers)
        assert r.status_code == 403

        # El admin sí
        # act + assert: el admin (autor) sí puede eliminarla (200).
        r = client.delete(f"/notas/{nota['id']}", headers=admin_headers)
        assert r.status_code == 200

    def test_autor_edita_y_archiva(self, client, admin_headers, cajero_headers):
        """El autor de una nota puede editarla y archivarla."""
        # arrange/act: la cajera (autora) crea una nota dirigida al admin.
        r = client.post(
            "/notas",
            json={"texto": "Se acabó el café", "destinatario": "admin", "prioridad": "alta"},
            headers=cajero_headers,
        )
        nota = r.json()
        # assert: el autor registrado es "Cajero".
        assert nota["autor_nombre"] == "Cajero"

        # act: la autora edita el texto y la archiva.
        r = client.patch(
            f"/notas/{nota['id']}",
            json={"texto": "Se acabó el café molido", "archivada": True},
            headers=cajero_headers,
        )
        # assert: la edición y el archivado se aplican correctamente.
        assert r.status_code == 200
        assert r.json()["archivada"] is True

    def test_filtros_y_resumen(self, client, admin_headers):
        """Los filtros por tipo y el resumen cuentan tareas y notas correctamente."""
        # arrange: dos tareas y una nota.
        client.post("/notas", json={"texto": "t1", "tipo": "tarea"}, headers=admin_headers)
        t2 = client.post(
            "/notas", json={"texto": "t2", "tipo": "tarea"}, headers=admin_headers
        ).json()
        client.post("/notas", json={"texto": "n1", "tipo": "nota"}, headers=admin_headers)

        # act + assert: el filtro tipo=tarea devuelve solo las 2 tareas.
        r = client.get("/notas?tipo=tarea", headers=admin_headers)
        assert len(r.json()) == 2

        # act + assert: el resumen cuenta 2 tareas pendientes, 1 nota y 3 pendientes.
        r = client.get("/notas/resumen", headers=admin_headers)
        data = r.json()
        assert data["tareas_pendientes"] == 2
        assert data["notas"] == 1
        assert data["pendientes"] == 3

        # Marcar una hecha y archivar una nota
        # act: marcamos la segunda tarea como hecha.
        client.patch(f"/notas/{t2['id']}", json={"hecho": True}, headers=admin_headers)
        # assert: ahora queda solo 1 tarea pendiente.
        r = client.get("/notas/resumen", headers=admin_headers)
        assert r.json()["tareas_pendientes"] == 1

    def test_filtro_destinatario_incluye_todos(self, client, admin_headers):
        """El filtro por destinatario incluye las notas dirigidas a 'todos'."""
        # arrange: una nota global (todos) y una solo para admin.
        client.post(
            "/notas", json={"texto": "global", "destinatario": "todos"}, headers=admin_headers
        )
        client.post(
            "/notas", json={"texto": "solo admin", "destinatario": "admin"}, headers=admin_headers
        )
        # act: filtramos por destinatario=admin.
        r = client.get("/notas?destinatario=admin", headers=admin_headers)
        # incluye la de admin y la de todos
        # assert: devuelve ambas (la de admin y la global).
        assert len(r.json()) == 2
        # act: filtramos por destinatario=cajero.
        r = client.get("/notas?destinatario=cajero", headers=admin_headers)
        # solo la de todos
        # assert: solo aparece la global.
        assert len(r.json()) == 1

    def test_texto_obligatorio(self, client, admin_headers):
        """Una nota con texto vacío no es válida (422)."""
        # act + assert: crear una nota con texto en blanco debe fallar.
        r = client.post("/notas", json={"texto": "   "}, headers=admin_headers)
        assert r.status_code == 422
