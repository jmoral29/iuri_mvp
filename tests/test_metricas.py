import pytest
from fastapi.testclient import TestClient
from datetime import date

@pytest.fixture(scope="module")
def supervisor_token(client: TestClient):
    # Crear usuario supervisor si no existe y loguear
    client.post(
        "/usuarios",
        json={
            "nombre_completo": "Super Visor",
            "correo": "super.visor@example.com",
            "password": "super1234",
            "rol": "supervisor"
        },
        headers={"Authorization": "Bearer <TOKEN_ADMIN_VALIDO>"}
    )
    login = client.post(
        "/login",
        data={"username": "super.visor@example.com", "password": "super1234"}
    )
    return login.json()["access_token"]

def test_reporte_abogado(client: TestClient, abogado_token):
    headers = {"Authorization": f"Bearer {abogado_token}"}
    res = client.get("/metricas/abogado", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["abogado"] == "ana.aboga@example.com"
    assert "causas" in data

def test_reporte_supervision(client: TestClient, supervisor_token):
    headers = {"Authorization": f"Bearer {supervisor_token}"}
    res = client.get("/metricas/supervision", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "resumen" in data
    assert isinstance(data["resumen"], list)
