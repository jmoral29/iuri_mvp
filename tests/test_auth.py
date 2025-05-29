from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_usuario_invalido():
    response = client.post("/login", data={
        "username": "correo_falso@ejemplo.com",
        "password": "clave123"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales inválidas"
