import json
import pytest
from fastapi.testclient import TestClient
from app import schemas

def test_registrar_usuario_y_perfil(client: TestClient):
    # 1) Registrar un nuevo usuario (rol admin necesario)
    # Primero creamos un admin directamente en DB o mediante crud; aquí asumimos que existe uno:
    # Para simplificar, hardcodeamos encabezado con token admin obtenido manualmente
    admin_token = "Bearer <TOKEN_ADMIN_VALIDO>"
    headers = {"Authorization": admin_token}

    payload = {
        "nombre_completo": "Juan Pérez",
        "correo": "juan.perez@example.com",
        "password": "segura123",
        "rol": "abogado"
    }
    res = client.post("/usuarios", json=payload, headers=headers)
    assert res.status_code == 200
    user_out = schemas.UsuarioOut(**res.json())
    assert user_out.correo == payload["correo"]
    assert user_out.rol == "abogado"
    assert user_out.activo is True

    # 2) Login con el nuevo usuario
    res2 = client.post(
        "/login",
        data={"username": payload["correo"], "password": payload["password"]},
    )
    assert res2.status_code == 200
    data = res2.json()
    assert "access_token" in data

    token = data["access_token"]
    headers_user = {"Authorization": f"Bearer {token}"}

    # 3) GET /me para recuperar perfil
    res3 = client.get("/me", headers=headers_user)
    assert res3.status_code == 200
    perfil = schemas.UsuarioOut(**res3.json())
    assert perfil.correo == payload["correo"]
    assert perfil.nombre_completo == payload["nombre_completo"]
