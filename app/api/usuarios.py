from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app import crud, schemas, auth
from app.db import get_db
from app.auth import TokenData, crear_token_de_acceso
import uuid
import datetime

router = APIRouter()

# ----------------------
# Usuarios: Registro, login, perfil y recuperación
# ----------------------

@router.post(
    "/usuarios",
    response_model=schemas.UsuarioOut,
    summary="Registrar un nuevo usuario",
    description="Crea un usuario en el sistema. Rol requerido: admin"
)
def registrar_usuario(
    usuario: schemas.UsuarioCreate,
    db: Session = Depends(get_db),
    current_user=Depends(auth.requiere_rol(["admin"]))
):
    existente = crud.obtener_usuario_por_correo(db, usuario.correo)
    if existente:
        raise HTTPException(status_code=400, detail="Correo ya registrado")
    return crud.crear_usuario(db, usuario)

@router.post(
    "/login",
    response_model=schemas.Token,
    summary="Autenticación de usuarios",
    description="Genera un token JWT al validar credenciales"
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    usuario = crud.obtener_usuario_por_correo(db, form_data.username)
    if not usuario or not auth.verificar_password(form_data.password, usuario.hash_contrasena):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    token = crear_token_de_acceso({"sub": usuario.correo, "rol": usuario.rol})
    return {"access_token": token, "token_type": "bearer"}

@router.get(
    "/me",
    response_model=schemas.UsuarioOut,
    summary="Perfil del usuario autenticado",
    description="Recupera datos del usuario que hizo la petición (token requerido)"
)
def leer_perfil(
    token_data: TokenData = Depends(auth.obtener_usuario_actual),
    db: Session = Depends(get_db)
):
    usuario = crud.obtener_usuario_por_correo(db, token_data.sub)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

# ----------------------
# Recuperación de contraseña
# ----------------------

# En un sistema real, enviar correo; aquí simulamos con BackgroundTasks

def enviar_email_reset(correo: str, token: str):
    # Implementar envío de correo en producción
    print(f"[Email simulado] A {correo}: token de reset {token}")

@router.post(
    "/password-reset/request",
    summary="Solicitar recuperación de contraseña",
    description="Envía un token de un solo uso para restablecer contraseña",
    status_code=status.HTTP_202_ACCEPTED
)
def solicitar_reset(
    background_tasks: BackgroundTasks,
    correo: schemas.EmailRequest,
    db: Session = Depends(get_db)
):
    usuario = crud.obtener_usuario_por_correo(db, correo.email)
    if not usuario:
        # No revelar existencia de usuario
        return {"mensaje": "Si el correo existe, se envió un token"}
    # Generar token único con expiry corto
    reset_token = str(uuid.uuid4())
    expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    crud.guardar_token_reset(db, usuario.id, reset_token, expiry)
    background_tasks.add_task(enviar_email_reset, usuario.correo, reset_token)
    return {"mensaje": "Si el correo existe, se envió un token"}

@router.post(
    "/password-reset/confirm",
    summary="Confirmar recuperación de contraseña",
    description="Valida token y actualiza contraseña"
)
def confirmar_reset(
    datos: schemas.PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    registro = crud.obtener_token_reset(db, datos.token)
    if not registro or registro.expiry < datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token inválido o expirado")
    crud.actualizar_contrasena(db, registro.user_id, datos.new_password)
    crud.eliminar_token_reset(db, datos.token)
    return {"mensaje": "Contraseña actualizada exitosamente"}
