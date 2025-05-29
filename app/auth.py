from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional

# ── Configuración ──────────────────────────────────────────────────────────────
SECRET_KEY = "clave-secreta-legal"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# ── Modelos Pydantic ────────────────────────────────────────────────────────────
class TokenData(BaseModel):
    sub: Optional[str] = None
    rol: Optional[str] = None

# ── Funciones de hashing ────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    """Hashea una contraseña en texto plano."""
    return pwd_context.hash(password)

def verificar_password(password: str, hashed: str) -> bool:
    """Verifica que la contraseña en texto plano coincida con su hash."""
    return pwd_context.verify(password, hashed)

# ── Funciones JWT ───────────────────────────────────────────────────────────────
def crear_token_de_acceso(data: dict, expires_delta: timedelta = None) -> str:
    """
    Crea un JWT con los datos de `data` (debe incluir al menos "sub" y "rol").
    expire en minutos según ACCESS_TOKEN_EXPIRE_MINUTES si no se pasa expires_delta.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verificar_token(token: str) -> Optional[dict]:
    """Intenta decodificar el JWT, devolviendo el payload o None si falla."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

# ── Dependencias de FastAPI ────────────────────────────────────────────────────
def obtener_usuario_actual(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    Depende de OAuth2PasswordBearer para extraer el token 'Bearer <token>'.
    Verifica y decodifica el JWT, devolviendo un TokenData con 'sub' y 'rol'.
    Lanza HTTPException(401) si el token es inválido o expirado.
    """
    payload = verificar_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    token_data = TokenData(sub=payload.get("sub"), rol=payload.get("rol"))
    if not token_data.sub or not token_data.rol:
        raise HTTPException(status_code=401, detail="Información de usuario incompleta en token")
    return token_data

def requiere_rol(roles_permitidos: list[str]):
    """
    Retorna una dependencia que verifica que el 'rol' del usuario esté en roles_permitidos.
    Lanza HTTPException(403) si no coincide.
    """
    def validador(usuario: TokenData = Depends(obtener_usuario_actual)):
        if usuario.rol not in roles_permitidos:
            raise HTTPException(status_code=403, detail="No tienes permiso para esta acción")
        return usuario
    return validador
