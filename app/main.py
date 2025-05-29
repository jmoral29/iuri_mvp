from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from dotenv import load_dotenv

from app.db import Base, engine
from app import models
from app.auth import crear_token_de_acceso
from app.api import endpoints, usuarios, metricas
from app.api.resumen import router as resumen_router  # <- tu nuevo router de resumen PDF
import os

# Cargar variables de entorno
load_dotenv()
print("TOKEN CARGADO:", os.getenv("HUGGINGFACE_API_TOKEN"))

# Crear las tablas automáticamente
Base.metadata.create_all(bind=engine)

# Inicializar FastAPI
app = FastAPI()

@app.get("/")
def root():
    return {"mensaje": "¡Iuri MVP procesal listo y modularizado!"}

# Routers
app.include_router(endpoints.router)
app.include_router(usuarios.router)
app.include_router(metricas.router)
app.include_router(resumen_router)

# Login simple con token
@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    usuarios_demo = {
        "andrea": {"password": "admin123", "rol": "admin"},
        "javier": {"password": "abogado456", "rol": "abogado"},
        "laura": {"password": "supervisor789", "rol": "supervisor"}
    }

    usuario = usuarios_demo.get(form_data.username)
    if not usuario or usuario["password"] != form_data.password:
        raise HTTPException(status_code=401, detail="Usuario o contraseña inválida")

    token = crear_token_de_acceso(
        data={"sub": form_data.username, "rol": usuario["rol"]},
        expires_delta=timedelta(minutes=60)
    )
    return {"access_token": token, "token_type": "bearer"}
