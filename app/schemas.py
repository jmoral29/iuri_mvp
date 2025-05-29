from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import date, datetime

# ════════════════════════════════════════════════
# 🧑‍⚖️ USUARIOS
# ════════════════════════════════════════════════

class UsuarioBase(BaseModel):
    nombre_completo: str
    correo: EmailStr
    rol: str  # Ej: "abogado", "admin", "supervisor"

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioLogin(BaseModel):
    correo: EmailStr
    password: str

class UsuarioOut(UsuarioBase):
    id: int
    activo: bool
    fecha_creacion: datetime

    model_config = {
        "from_attributes": True
    }

class Token(BaseModel):
    access_token: str
    token_type: str

# ════════════════════════════════════════════════
# 📂 CAUSAS
# ════════════════════════════════════════════════

class CausaBase(BaseModel):
    rit: str
    representado: str
    tribunal: str
    abogado_responsable: str
    fecha_ingreso: date

class CausaCreate(CausaBase):
    pass

class CausaOut(CausaBase):
    id: int

    model_config = {
        "from_attributes": True
    }

# ════════════════════════════════════════════════
# ✅ TAREAS / CHECKLIST
# ════════════════════════════════════════════════

class ChecklistTareaBase(BaseModel):
    tarea_nombre: str
    completada: bool = False
    comentarios: Optional[str] = None
    fecha_completada: Optional[date] = None

class ChecklistTareaUpdate(BaseModel):
    completada: bool
    comentarios: Optional[str] = None
    fecha_completada: Optional[date] = None

class ChecklistTareaOut(ChecklistTareaBase):
    id: int
    causa_id: int

    model_config = {
        "from_attributes": True
    }
class EmailRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: constr(min_length=8)
