"""
Modelo de Proveedor (app/database/models/compras/proveedor.py)

Estructura DDL:
    CREATE TABLE compras.proveedores (
        id_proveedor SERIAL PRIMARY KEY,
        razon_social VARCHAR(250) NOT NULL,
        nit VARCHAR(50),
        telefono VARCHAR(50),
        correo VARCHAR(150),
        direccion TEXT,
        estado BOOLEAN DEFAULT TRUE
    );
"""

from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DatabaseSchema
from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.compras.compra import Compra


class Proveedor(Base):
    """
    Entidad Proveedor en el esquema 'compras'.
    """
    __tablename__ = "proveedores"
    __table_args__ = {"schema": DatabaseSchema.COMPRAS.value}

    id_proveedor: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    razon_social: Mapped[str] = mapped_column(String(250), nullable=False)
    nit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    correo: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    direccion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estado: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relaciones
    compras: Mapped[List["Compra"]] = relationship("Compra", back_populates="proveedor")

    def __repr__(self) -> str:
        return f"<Proveedor(id_proveedor={self.id_proveedor}, razon_social='{self.razon_social}')>"
