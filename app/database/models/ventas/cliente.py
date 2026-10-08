"""
Modelo de Cliente (app/database/models/ventas/cliente.py)

Estructura DDL:
    CREATE TABLE ventas.clientes (
        id_cliente SERIAL PRIMARY KEY,
        tipo_documento VARCHAR(20),
        numero_documento VARCHAR(50),
        nombre VARCHAR(150),
        apellido VARCHAR(150),
        telefono VARCHAR(50),
        correo VARCHAR(150),
        direccion TEXT,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DatabaseSchema
from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.ventas.venta import Venta


class Cliente(Base):
    """
    Entidad Cliente en el esquema 'ventas'.
    """
    __tablename__ = "clientes"
    __table_args__ = {"schema": DatabaseSchema.VENTAS.value}

    id_cliente: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tipo_documento: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    numero_documento: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    nombre: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    apellido: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    correo: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    direccion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )

    # Relaciones
    ventas: Mapped[List["Venta"]] = relationship("Venta", back_populates="cliente")

    def __repr__(self) -> str:
        return f"<Cliente(id_cliente={self.id_cliente}, doc='{self.numero_documento}', nombre='{self.nombre}')>"
