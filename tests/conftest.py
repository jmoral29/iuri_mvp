import pytest
from fastapi.testclient import TestClient
from app.main import app
import sys
import os
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def client():
    return TestClient(app)
    
def test_login(client):
    response = client.post("/login", data={...})
