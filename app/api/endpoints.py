from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app import crud, schemas
from app.db import get_db
from app.auth import requiere_rol
import pandas as pd
from io import BytesIO
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import os

router = APIRouter()

# ----------------------
# Endpoints de Causas
# ----------------------

@router.get(
    "/causas",
    response_model=list[schemas.CausaOut],
    summary="Listar todas las causas",
    description="Devuelve todas las causas registradas. Rol: admin, abogado, supervisor"
)
def listar_causas(
    db: Session = Depends(get_db),
    usuario = Depends(requiere_rol(["admin", "abogado", "supervisor"]))
):
    return crud.listar_causas(db)

@router.post(
    "/causas",
    response_model=schemas.CausaOut,
    summary="Crear una nueva causa",
    description="Crea una causa y genera su checklist base. Rol: admin, abogado"
)
def crear_causa(
    causa: schemas.CausaCreate,
    db: Session = Depends(get_db),
    usuario = Depends(requiere_rol(["admin", "abogado"]))
):
    nueva = crud.crear_causa(db, causa)
    crud.crear_checklist_base(db, nueva.id)
    return nueva

@router.get(
    "/causas/{causa_id}",
    response_model=schemas.CausaOut,
    summary="Obtener detalle de una causa",
    description="Recupera una causa por su ID. Rol: admin, abogado, supervisor"
)
def obtener_causa(
    causa_id: int,
    db: Session = Depends(get_db),
    usuario = Depends(requiere_rol(["admin", "abogado", "supervisor"]))
):
    causa = crud.obtener_causa(db, causa_id)
    if not causa:
        raise HTTPException(status_code=404, detail="Causa no encontrada")
    return causa

# ----------------------
# Importar desde Excel
# ----------------------

@router.post(
    "/importar-causas",
    summary="Importar causas desde un archivo Excel",
    description="Carga múltiples causas desde .xlsx y genera checklist. Rol: admin, abogado"
)
async def importar_causas(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario = Depends(requiere_rol(["admin", "abogado"]))
):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="El archivo debe ser .xlsx")

    contents = await file.read()
    try:
        df = pd.read_excel(BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo leer el archivo: {e}")

    requeridas = ["RIT", "Representado", "Tribunal", "Abogado responsable", "Fecha ingreso"]
    if not all(col in df.columns for col in requeridas):
        raise HTTPException(status_code=400, detail="Faltan columnas requeridas en la planilla")

    errores = []
    creadas = 0
    for idx, row in df.iterrows():
        try:
            causa_data = schemas.CausaCreate(
                rit=str(row["RIT"]),
                representado=row["Representado"],
                tribunal=row["Tribunal"],
                abogado_responsable=row["Abogado responsable"],
                fecha_ingreso=pd.to_datetime(row["Fecha ingreso"]).date()
            )
            nueva = crud.crear_causa(db, causa_data)
            crud.crear_checklist_base(db, nueva.id)
            creadas += 1
        except Exception as e:
            errores.append(f"Fila {idx+2}: {e}")
            db.rollback()

    if errores:
        raise HTTPException(status_code=422, detail={"creadas": creadas, "errores": errores})
    return {"mensaje": f"Se importaron {creadas} causas correctamente"}

# ----------------------
# Checklist por Causa
# ----------------------

@router.get(
    "/causas/{causa_id}/checklist",
    response_model=list[schemas.ChecklistTareaOut],
    summary="Listar checklist de una causa",
    description="Recupera todas las tareas del checklist de una causa. Rol: admin, abogado, supervisor"
)
def ver_checklist(
    causa_id: int,
    db: Session = Depends(get_db),
    usuario = Depends(requiere_rol(["admin", "abogado", "supervisor"]))
):
    tareas = crud.obtener_checklist_por_causa(db, causa_id)
    if not tareas:
        raise HTTPException(status_code=404, detail="No hay checklist para esta causa")
    return tareas

# ----------------------
# Actualizar Tarea
# ----------------------

@router.put(
    "/tareas/{tarea_id}",
    response_model=schemas.ChecklistTareaOut,
    summary="Actualizar una tarea del checklist",
    description="Permite marcar completada, añadir comentarios y fecha. Rol: admin, abogado"
)
def actualizar_estado_tarea(
    tarea_id: int,
    datos: schemas.ChecklistTareaUpdate,
    db: Session = Depends(get_db),
    usuario = Depends(requiere_rol(["admin", "abogado"]))
):
    tarea = crud.actualizar_tarea(db, tarea_id, datos)
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return tarea

router = APIRouter()    

HF_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

class TextoEntrada(BaseModel):
    texto: str

@router.post("/resumir/")
def resumir_texto(data: TextoEntrada):
    payload = {"inputs": data.texto}
    response = requests.post(API_URL, headers=HEADERS, json=payload)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    resultado = response.json()
    if isinstance(resultado, list) and "summary_text" in resultado[0]:
        return {"resumen": resultado[0]["summary_text"]}
    else:
        return {"detalle": resultado}