"""
Modelo de Marca (app/database/models/inventario/marca.py)

Estructura DDL:
    CREATE TABLE inventario.marcas (
        id_marca SERIAL PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL UNIQUE,
        estado BOOLEAN DEFAULT TRUE
    );
"""

from typing import TYPE_CHECKING, List
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DatabaseSchema
from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.inventario.producto import Producto


class Marca(Base):
    """
    Marca de productos en el esquema 'inventario'.
    """
    __tablename__ = "marcas"
    __table_args__ = {"schema": DatabaseSchema.INVENTARIO.value}

    id_marca: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    estado: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relaciones
    productos: Mapped[List["Producto"]] = relationship("Producto", back_populates="marca")

    def __repr__(self) -> str:
        return f"<Marca(id_marca={self.id_marca}, nombre='{self.nombre}', estado={self.estado})>"
