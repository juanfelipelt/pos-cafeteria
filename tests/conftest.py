"""Configuración compartida de pytest para toda la suite de pruebas.

Este archivo se llama conftest.py y es especial para pytest: se carga de forma
automática y todo lo que definamos aquí queda disponible en TODAS las pruebas,
sin necesidad de importarlo.

Hace tres cosas:
1. Prepara un entorno aislado ANTES de importar la app: crea una base de datos
   SQLite temporal y define variables de entorno de prueba, para no tocar datos
   reales.
2. Define fixtures reutilizables (base de datos limpia, cliente HTTP y cabeceras
   con token de admin y de cajero).
3. Garantiza que cada prueba empiece desde un estado conocido (base vacía y
   usuario admin sembrado), para que las pruebas no dependan entre sí.
"""

import os
import tempfile

# Creamos un archivo temporal que servirá como base de datos SQLite de pruebas.
# mkstemp devuelve un descriptor de archivo (_fd) y la ruta del archivo (_db_path).
_fd, _db_path = tempfile.mkstemp(suffix=".db")
# Cerramos el descriptor: la app abrirá la base por su ruta, no por este handle.
os.close(_fd)
# Apuntamos la aplicación a la base temporal (no a la base real de desarrollo).
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"
# Clave para firmar los JWT en pruebas (debe tener al menos 32 bytes).
os.environ["SECRET_KEY"] = "clave-secreta-de-prueba-muy-larga-32bytes-min"
# Credenciales del administrador que se sembrará en cada prueba.
os.environ["ADMIN_EMAIL"] = "admin@cafeteriapos.com"
os.environ["ADMIN_PASSWORD"] = "admin123"

# Importamos la app DESPUÉS de definir el entorno, porque al importarla se lee
# la configuración (DATABASE_URL, SECRET_KEY, ...). Si importáramos antes, la
# app usaría la base de datos real.
import pytest
from fastapi.testclient import TestClient

from app import _seed_admin, app
from config import settings
from database import Base, engine
# Esta importación registra los modelos en Base, para que create_all conozca las tablas.
import infrastructure.models  # noqa: F401


@pytest.fixture(autouse=True)
def _reset_db():
    """Deja la base de datos limpia antes de CADA prueba.

    autouse=True hace que pytest la ejecute sola, sin que el test la pida.
    Borra todas las tablas, las vuelve a crear y siembra el usuario admin, para
    que cada prueba arranque desde cero y no dependa de las anteriores.
    """
    # arrange: dejamos un estado conocido (sin datos, con el usuario admin).
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    _seed_admin()
    # En el yield se ejecuta la prueba; al terminar, la ejecución continúa aquí.
    yield


@pytest.fixture(scope="session")
def client():
    """Cliente HTTP de pruebas que simula llamadas reales a la API.

    scope="session" significa que se crea una sola vez para toda la sesión de
    pruebas (levantar la app es costoso). Se usa 'with' para que FastAPI ejecute
    sus eventos de inicio y apagado (startup/shutdown).
    """
    # Abre la aplicación en modo pruebas y la entrega como cliente.
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def admin_headers(client):
    """Devuelve las cabeceras HTTP con el token JWT del administrador.

    Muchos endpoints exigen ser admin. Esta fixture inicia sesión con las
    credenciales sembradas y construye el header Authorization listo para usar.
    """
    # act: pedimos el login del admin a la API.
    r = client.post(
        "/auth/login",
        json={"email": settings.admin_email, "password": settings.admin_password},
    )
    # assert: el login debe responder correctamente.
    assert r.status_code == 200
    # Extraemos el token y lo envolvemos en el formato "Bearer" que espera la API.
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def cajero_headers(client, admin_headers):
    """Devuelve las cabeceras HTTP con el token JWT de un usuario cajero.

    Se usa para comprobar que un cajero NO puede ejecutar acciones de admin
    (permisos) y SÍ puede hacer las permitidas (por ejemplo, crear ventas).
    Depende de admin_headers porque solo un admin puede registrar usuarios.
    """
    # act: el admin registra un nuevo usuario con rol "cajero".
    r = client.post(
        "/auth/registro",
        json={
            "nombre": "Cajero",
            "email": "cajero@cafeteriapos.com",
            "password": "cajero123",
            "rol": "cajero",
        },
        headers=admin_headers,
    )
    # assert: el registro fue exitoso.
    assert r.status_code == 200
    # act: iniciamos sesión como el cajero para obtener su token.
    r = client.post(
        "/auth/login",
        json={"email": "cajero@cafeteriapos.com", "password": "cajero123"},
    )
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
