import pytest
from fastapi.testclient import TestClient
from app import schemas

@pytest.fixture(scope="module")
def abogado_token(client: TestClient):
    # Crear o usar un usuario abogado ya en DB; aquí registramos uno rápido
    res = client.post(
        "/usuarios",
        json={
            "nombre_completo": "Ana Aboga",
            "correo": "ana.aboga@example.com",
            "password": "password123",
            "rol": "abogado"
        },
        headers={"Authorization": "Bearer <TOKEN_ADMIN_VALIDO>"}
    )
    # Login para obtener token
    login = client.post(
        "/login",
        data={"username": "ana.aboga@example.com", "password": "password123"}
    )
    return login.json()["access_token"]

def test_crear_listar_obtener_causa(client: TestClient, abogado_token):
    headers = {"Authorization": f"Bearer {abogado_token}"}
    # Crear causa
    payload = {
        "rit": "C-2025-0001",
        "representado": "Cliente X",
        "tribunal": "Juzgado Civil",
        "abogado_responsable": "ana.aboga@example.com",
        "fecha_ingreso": "2025-05-27"
    }
    res = client.post("/causas", json=payload, headers=headers)
    assert res.status_code == 200
    causa = schemas.CausaOut(**res.json())
    assert causa.rit == payload["rit"]
    causa_id = causa.id

    # Listar causas
    res2 = client.get("/causas", headers=headers)
    assert res2.status_code == 200
    lista = res2.json()
    assert any(c["id"] == causa_id for c in lista)

    # Obtener causa por ID
    res3 = client.get(f"/causas/{causa_id}", headers=headers)
    assert res3.status_code == 200
    detalle = schemas.CausaOut(**res3.json())
    assert detalle.id == causa_id

def test_checklist_generado(client: TestClient, abogado_token):
    headers = {"Authorization": f"Bearer {abogado_token}"}
    # Usamos la primera causa de la lista
    res = client.get("/causas", headers=headers)
    causa = res.json()[0]
    causa_id = causa["id"]

    # GET /causas/{id}/checklist
    res2 = client.get(f"/causas/{causa_id}/checklist", headers=headers)
    assert res2.status_code == 200
    tareas = [schemas.ChecklistTareaOut(**t) for t in res2.json()]
    assert len(tareas) == 3
    nombres = [t.tarea_nombre for t in tareas]
    assert "Revisar patrocinio" in nombres
