"""
Modelo de Categoría (app/database/models/inventario/categoria.py)

Estructura DDL:
    CREATE TABLE inventario.categorias (
        id_categoria SERIAL PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL UNIQUE,
        descripcion TEXT,
        estado BOOLEAN DEFAULT TRUE,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DatabaseSchema
from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.inventario.producto import Producto


class Categoria(Base):
    """
    Categoría de productos en el esquema 'inventario'.
    """
    __tablename__ = "categorias"
    __table_args__ = {"schema": DatabaseSchema.INVENTARIO.value}

    id_categoria: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estado: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )

    # Relaciones
    productos: Mapped[List["Producto"]] = relationship("Producto", back_populates="categoria")

    def __repr__(self) -> str:
        return f"<Categoria(id_categoria={self.id_categoria}, nombre='{self.nombre}', estado={self.estado})>"
