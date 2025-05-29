from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, timedelta
from app.db import get_db
from app import models, auth
from app.auth import requiere_rol

router = APIRouter()

# ----------------------
# Métricas de cumplimiento semanal
# ----------------------

@router.get("/metricas/abogado", summary="Reporte personal del abogado")
def reporte_abogado(
    usuario=Depends(requiere_rol(["abogado"])),
    db: Session = Depends(get_db)
):
    hoy = date.today()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)

    causas = db.query(models.Causa).filter(models.Causa.abogado_responsable == usuario.sub).all()
    resumen = []

    for causa in causas:
        tareas = db.query(models.ChecklistTarea).filter(models.ChecklistTarea.causa_id == causa.id).all()
        total = len(tareas)
        completadas = sum(1 for t in tareas if t.completada and t.fecha_completada and inicio_semana <= t.fecha_completada <= fin_semana)
        pendiente = total - completadas
        resumen.append({
            "rit": causa.rit,
            "representado": causa.representado,
            "total_tareas": total,
            "completadas_semana": completadas,
            "pendientes": pendiente,
            "estado": "✅" if completadas == total else "🟡" if completadas > 0 else "🔴"
        })

    return {
        "abogado": usuario.sub,
        "semana": f"{inicio_semana} a {fin_semana}",
        "causas": resumen
    }

@router.get("/metricas/supervision", summary="Reporte supervisor de todos los abogados")
def reporte_supervision(
    usuario=Depends(requiere_rol(["supervisor", "admin"])),
    db: Session = Depends(get_db)
):
    hoy = date.today()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)

    abogados = db.query(models.Usuario).filter(models.Usuario.rol == "abogado").all()
    reportes = []

    for ab in abogados:
        causas = db.query(models.Causa).filter(models.Causa.abogado_responsable == ab.correo).all()
        completadas_total = 0
        tareas_total = 0
        detalle = []

        for causa in causas:
            tareas = db.query(models.ChecklistTarea).filter(models.ChecklistTarea.causa_id == causa.id).all()
            completadas = sum(1 for t in tareas if t.completada and t.fecha_completada and inicio_semana <= t.fecha_completada <= fin_semana)
            detalle.append({"rit": causa.rit, "completadas": completadas, "total": len(tareas)})
            completadas_total += completadas
            tareas_total += len(tareas)

        porcentaje = round((completadas_total / tareas_total) * 100, 1) if tareas_total else 0
        reportes.append({
            "abogado": ab.nombre_completo,
            "correo": ab.correo,
            "total_tareas": tareas_total,
            "completadas_semana": completadas_total,
            "porcentaje": porcentaje,
            "detalle": detalle,
            "estado": "✅" if porcentaje == 100 else "🟡" if porcentaje >= 50 else "🔴"
        })

    return {
        "semana": f"{inicio_semana} a {fin_semana}",
        "resumen": reportes
    }
