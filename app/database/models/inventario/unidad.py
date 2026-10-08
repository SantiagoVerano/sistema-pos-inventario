"""
Modelo de Unidad (app/database/models/inventario/unidad.py)

Estructura DDL:
    CREATE TABLE inventario.unidades (
        id_unidad SERIAL PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL UNIQUE,
        abreviatura VARCHAR(10)
    );
"""

from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DatabaseSchema
from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.inventario.producto import Producto


class Unidad(Base):
    """
    Unidad de medida en el esquema 'inventario'.
    """
    __tablename__ = "unidades"
    __table_args__ = {"schema": DatabaseSchema.INVENTARIO.value}

    id_unidad: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    abreviatura: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Relaciones
    productos: Mapped[List["Producto"]] = relationship("Producto", back_populates="unidad")

    def __repr__(self) -> str:
        return f"<Unidad(id_unidad={self.id_unidad}, nombre='{self.nombre}', abreviatura='{self.abreviatura}')>"
