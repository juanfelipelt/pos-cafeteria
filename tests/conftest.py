import os
import tempfile

_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.close(_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"
os.environ["SECRET_KEY"] = "clave-secreta-de-prueba-muy-larga-32bytes-min"
os.environ["ADMIN_EMAIL"] = "admin@cafeteriapos.com"
os.environ["ADMIN_PASSWORD"] = "admin123"

import pytest
from fastapi.testclient import TestClient

from app import _seed_admin, app
from config import settings
from database import Base, engine
import infrastructure.models  # noqa: F401


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    _seed_admin()
    yield


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def admin_headers(client):
    r = client.post(
        "/auth/login",
        json={"email": settings.admin_email, "password": settings.admin_password},
    )
    assert r.status_code == 200
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def cajero_headers(client, admin_headers):
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
    assert r.status_code == 200
    r = client.post(
        "/auth/login",
        json={"email": "cajero@cafeteriapos.com", "password": "cajero123"},
    )
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
