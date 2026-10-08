"""
Modelo de Usuario (app/database/models/seguridad/usuario.py)

Estructura DDL:
    CREATE TABLE seguridad.usuarios (
        id_usuario SERIAL PRIMARY KEY,
        nombre VARCHAR(150) NOT NULL,
        correo VARCHAR(150) NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        activo BOOLEAN DEFAULT TRUE,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
"""

from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DatabaseSchema
from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.seguridad.rol import UsuarioRol
    from app.database.models.inventario.movimiento_inventario import MovimientoInventario
    from app.database.models.compras.compra import Compra
    from app.database.models.ventas.venta import Venta


class Usuario(Base):
    """
    Entidad de usuario en el esquema 'seguridad'.
    """
    __tablename__ = "usuarios"
    __table_args__ = {"schema": DatabaseSchema.SEGURIDAD.value}

    id_usuario: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    correo: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )

    # Relaciones ORM
    roles_asociados: Mapped[List["UsuarioRol"]] = relationship(
        "UsuarioRol", back_populates="usuario", cascade="all, delete-orphan"
    )
    movimientos_inventario: Mapped[List["MovimientoInventario"]] = relationship(
        "MovimientoInventario", back_populates="usuario"
    )
    compras: Mapped[List["Compra"]] = relationship("Compra", back_populates="usuario")
    ventas: Mapped[List["Venta"]] = relationship("Venta", back_populates="usuario")

    def __repr__(self) -> str:
        return f"<Usuario(id_usuario={self.id_usuario}, correo='{self.correo}', activo={self.activo})>"
