from fastapi import APIRouter, File, UploadFile
import requests
from PyPDF2 import PdfReader
import io
import os

router = APIRouter()

HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")

@router.post("/resumen-pdf/")
async def resumir_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return {"error": "Solo se permiten archivos PDF"}

    # Leer el contenido del PDF
    contenido = await file.read()
    lector_pdf = PdfReader(io.BytesIO(contenido))
    texto = ""
    for pagina in lector_pdf.pages:
        texto += pagina.extract_text() or ""

    # Acotar el texto si es muy largo (FLAN-T5 tiene límite de tokens)
    texto = texto[:3000]  # puedes ajustar este límite si quieres

    # Prompt personalizado
    prompt = f"Resume el siguiente texto legal en 3 puntos clave:\n\n{texto}"

    # Enviar al endpoint de Hugging Face
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
    payload = {"inputs": prompt}

    response = requests.post(
        "https://api-inference.huggingface.co/models/google/flan-t5-base",
        headers=headers,
        json=payload
    )

    if response.status_code != 200:
        return {"error": "Error al generar resumen", "detalle": response.json()}

    resultado = response.json()
    resumen = resultado[0]["generated_text"]

    return {"resumen": resumen}
