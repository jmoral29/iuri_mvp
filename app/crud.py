from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date, datetime
from app import models, schemas, auth

# ════════════════════════════════════════════════
# 🧑‍⚖️ USUARIOS
# ════════════════════════════════════════════════

def crear_usuario(db: Session, user_data: schemas.UsuarioCreate) -> models.Usuario:
    hashed = auth.hash_password(user_data.password)
    user = models.Usuario(
        nombre_completo=user_data.nombre_completo,
        correo=user_data.correo,
        hashed_password=hashed,
        rol=user_data.rol,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def obtener_usuario_por_correo(db: Session, correo: str) -> models.Usuario | None:
    return db.query(models.Usuario).filter(models.Usuario.correo == correo).first()


def autenticar_usuario(db: Session, correo: str, password: str) -> models.Usuario | None:
    user = obtener_usuario_por_correo(db, correo)
    if not user or not auth.verificar_password(password, user.hashed_password):
        return None
    return user


def listar_usuarios(db: Session):
    return db.query(models.Usuario).all()


def actualizar_usuario(db: Session, usuario_id: int, activo: bool = None, nuevo_rol: str = None):
    user = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not user:
        return None
    if activo is not None:
        user.activo = activo
    if nuevo_rol:
        user.rol = nuevo_rol
    db.commit()
    db.refresh(user)
    return user

# ════════════════════════════════════════════════
# 📂 CAUSAS
# ════════════════════════════════════════════════

def crear_causa(db: Session, causa_data: schemas.CausaCreate):
    nueva = models.Causa(**causa_data.dict())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


def listar_causas(db: Session):
    return db.query(models.Causa).all()


def obtener_causa(db: Session, causa_id: int):
    return db.query(models.Causa).filter(models.Causa.id == causa_id).first()


def listar_causas_por_abogado(db: Session, abogado_nombre: str):
    return db.query(models.Causa).filter(models.Causa.abogado_responsable == abogado_nombre).all()

# ════════════════════════════════════════════════
# ✅ TAREAS / CHECKLIST
# ════════════════════════════════════════════════

def crear_checklist_base(db: Session, causa_id: int):
    tareas = [
        "Revisar patrocinio",
        "Contestación de demanda",
        "Verificar tramitación"
    ]
    for nombre in tareas:
        tarea = models.ChecklistTarea(
            causa_id=causa_id,
            tarea_nombre=nombre
        )
        db.add(tarea)
    db.commit()


def obtener_checklist_por_causa(db: Session, causa_id: int):
    return db.query(models.ChecklistTarea).filter(models.ChecklistTarea.causa_id == causa_id).all()


def actualizar_tarea(db: Session, tarea_id: int, datos: schemas.ChecklistTareaUpdate):
    tarea = db.query(models.ChecklistTarea).filter(models.ChecklistTarea.id == tarea_id).first()
    if not tarea:
        return None
    tarea.completada = datos.completada
    tarea.comentarios = datos.comentarios
    if datos.completada:
        tarea.fecha_completada = datos.fecha_completada or date.today()
    else:
        tarea.fecha_completada = None
    db.commit()
    db.refresh(tarea)
    return tarea


def actualizar_tarea_por_nombre(db: Session, causa_id: int, tarea_nombre: str, datos: schemas.ChecklistTareaUpdate):
    tarea = db.query(models.ChecklistTarea).filter(
        and_(
            models.ChecklistTarea.causa_id == causa_id,
            models.ChecklistTarea.tarea_nombre == tarea_nombre
        )
    ).first()
    if not tarea:
        return None
    tarea.completada = datos.completada
    tarea.comentarios = datos.comentarios
    if datos.completada:
        tarea.fecha_completada = datos.fecha_completada or date.today()
    else:
        tarea.fecha_completada = None
    db.commit()
    db.refresh(tarea)
    return tarea


def filtrar_tareas(db: Session, abogado: str | None = None, causa_id: int | None = None, completada: bool | None = None):
    query = db.query(models.ChecklistTarea).join(models.Causa)
    if abogado:
        query = query.filter(models.Causa.abogado_responsable == abogado)
    if causa_id:
        query = query.filter(models.ChecklistTarea.causa_id == causa_id)
    if completada is not None:
        query = query.filter(models.ChecklistTarea.completada == completada)
    return query.all()


def tareas_por_abogado(db: Session, abogado_nombre: str):
    return (
        db.query(models.ChecklistTarea)
        .join(models.Causa)
        .filter(models.Causa.abogado_responsable == abogado_nombre)
        .all()
    )

# ════════════════════════════════════════════════
# 🔒 RECUPERACIÓN DE CONTRASEÑA
# ════════════════════════════════════════════════

def guardar_token_reset(db: Session, user_id: int, token: str, expiry: datetime):
    nuevo = models.PasswordResetToken(
        user_id=user_id,
        token=token,
        expiry=expiry
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_token_reset(db: Session, token: str):
    return db.query(models.PasswordResetToken).filter(models.PasswordResetToken.token == token).first()


def actualizar_contrasena(db: Session, user_id: int, new_password: str):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    if usuario:
        usuario.hashed_password = auth.hash_password(new_password)
        db.commit()
        db.refresh(usuario)
    return usuario


def eliminar_token_reset(db: Session, token: str):
    registro = db.query(models.PasswordResetToken).filter(models.PasswordResetToken.token == token).first()
    if registro:
        db.delete(registro)
        db.commit()
    return None
