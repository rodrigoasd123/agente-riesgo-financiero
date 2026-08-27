"""Integración de SPEC-007: RBAC, usuarios persistentes y sesiones revocables."""

from pathlib import Path

import bcrypt
import pytest
from fastapi.testclient import TestClient

import backend.db.database as database
from backend.auth.security import create_access_token
from backend.main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "security.db"))
    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, username: str = "admin", password: str = "admin123") -> dict[str, str]:
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_analyst(client: TestClient, admin_headers: dict[str, str], username: str = "analista_prueba") -> dict:
    response = client.post(
        "/auth/users",
        json={"username": username, "password": "Analista-1234", "role": "analyst"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()


def test_bootstrap_login_y_jwt_con_rol_y_sesion(client: TestClient):
    response = client.post("/auth/login", json={"username": "ADMIN", "password": "admin123"})
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "admin"
    assert body["role"] == "admin"
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json() == {"username": "admin", "role": "admin"}


def test_admin_crea_analista_sin_exponer_password_ni_hash(client: TestClient):
    headers = login(client)
    public_user = create_analyst(client, headers)
    assert public_user["username"] == "analista_prueba"
    assert public_user["role"] == "analyst"
    assert "password" not in public_user
    assert "hash" not in public_user

    stored = database.obtener_usuario("analista_prueba")
    assert stored is not None
    assert stored["password_hash"] != "Analista-1234"
    assert int(stored["password_hash"].split("$")[2]) >= 12
    assert bcrypt.checkpw(b"Analista-1234", stored["password_hash"].encode("utf-8"))

    duplicate = client.post(
        "/auth/users",
        json={"username": "ANALISTA_PRUEBA", "password": "Otra-clave-123", "role": "analyst"},
        headers=headers,
    )
    assert duplicate.status_code == 409


def test_analista_accede_negocio_pero_no_administracion(client: TestClient):
    admin_headers = login(client)
    create_analyst(client, admin_headers)
    analyst_headers = login(client, "analista_prueba", "Analista-1234")

    assert client.get("/analyses", headers=analyst_headers).status_code == 200
    assert client.get("/settings/capabilities", headers=analyst_headers).status_code == 200
    assert client.get("/settings/status", headers=analyst_headers).status_code == 403
    assert client.get("/auth/users", headers=analyst_headers).status_code == 403
    assert client.post("/settings/gmail/authorize", headers=analyst_headers).status_code == 403


def test_logout_revoca_token_actual(client: TestClient):
    headers = login(client)
    assert client.post("/auth/logout", headers=headers).status_code == 204
    assert client.get("/auth/me", headers=headers).status_code == 401


def test_desactivar_usuario_revoca_sesiones_y_bloquea_login(client: TestClient):
    admin_headers = login(client)
    create_analyst(client, admin_headers)
    analyst_headers = login(client, "analista_prueba", "Analista-1234")

    disabled = client.patch(
        "/auth/users/analista_prueba/active",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert disabled.status_code == 200
    assert disabled.json()["is_active"] is False
    assert client.get("/auth/me", headers=analyst_headers).status_code == 401
    failed_login = client.post(
        "/auth/login", json={"username": "analista_prueba", "password": "Analista-1234"}
    )
    assert failed_login.status_code == 401
    assert failed_login.json()["detail"] == "Usuario o contrasenia incorrectos"


def test_admin_no_puede_desactivarse_a_si_mismo(client: TestClient):
    headers = login(client)
    response = client.patch(
        "/auth/users/admin/active", json={"is_active": False}, headers=headers
    )
    assert response.status_code == 409
    assert client.get("/auth/me", headers=headers).status_code == 200


def test_token_sin_sesion_y_rol_obsoleto_fallan_cerrados(client: TestClient):
    unknown_session = create_access_token("admin", "admin")
    assert client.get(
        "/auth/me", headers={"Authorization": f"Bearer {unknown_session}"}
    ).status_code == 401

    admin_headers = login(client)
    with database.get_connection() as conn:
        conn.execute("UPDATE users SET role = 'analyst' WHERE username = 'admin'")
    assert client.get("/auth/me", headers=admin_headers).status_code == 401


def test_analisis_permanece_aislado_entre_admin_y_analista(client: TestClient):
    admin_headers = login(client)
    create_analyst(client, admin_headers)
    analyst_headers = login(client, "analista_prueba", "Analista-1234")
    database.guardar_analisis(
        analysis_id="privado-analista",
        filename="privado.pdf",
        created_by="analista_prueba",
        cifras={"ventas": 10},
        indicadores={},
        alertas=[],
        resumen="privado",
        chunks=["[Pagina 1] Ventas: 10"],
    )

    analyst_history = client.get("/analyses", headers=analyst_headers).json()["analyses"]
    admin_history = client.get("/analyses", headers=admin_headers).json()["analyses"]
    assert [item["id"] for item in analyst_history] == ["privado-analista"]
    assert all(item["id"] != "privado-analista" for item in admin_history)
    forbidden_export = client.post(
        "/analyses/privado-analista/report/pdf", headers=admin_headers
    )
    assert forbidden_export.status_code == 404
