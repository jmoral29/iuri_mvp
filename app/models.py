from sqlalchemy import Column, Integer, String, Date
from app.db import Base

class Causa(Base):
    __tablename__ = "causas"

    id = Column(Integer, primary_key=True, index=True)
    rit = Column(String, nullable=False)
    representado = Column(String, nullable=False)
    tribunal = Column(String, nullable=False)
    abogado_responsable = Column(String, nullable=False)
    fecha_ingreso = Column(Date, nullable=False)

from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship

# ya tenés la clase Causa

class ChecklistTarea(Base):
    __tablename__ = "checklist_tareas"

    id = Column(Integer, primary_key=True, index=True)
    causa_id = Column(Integer, ForeignKey("causas.id"), nullable=False)

    tarea_nombre = Column(String, nullable=False)
    completada = Column(Boolean, default=False)
    comentarios = Column(String, nullable=True)
    fecha_completada = Column(Date, nullable=True)

    causa = relationship("Causa", backref="checklist")

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from app.db import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre_completo = Column(String, nullable=False)
    correo = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    rol = Column(String, nullable=False)            # abogado | supervisor | admin
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)