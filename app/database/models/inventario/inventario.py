"""
Modelo de Inventario (app/database/models/inventario/inventario.py)

Estructura DDL:
    CREATE TABLE inventario.inventario (
        id_producto INT PRIMARY KEY REFERENCES inventario.productos(id_producto) ON DELETE CASCADE,
        stock_actual INT NOT NULL CHECK (stock_actual >= 0),
        fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
"""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DatabaseSchema
from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.inventario.producto import Producto


class Inventario(Base):
    """
    Tabla 'inventario.inventario' para balance de existencias físicas.
    """
    __tablename__ = "inventario"
    __table_args__ = (
        CheckConstraint("stock_actual >= 0", name="chk_stock_actual_positivo"),
        {"schema": DatabaseSchema.INVENTARIO.value}
    )

    id_producto: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(f"{DatabaseSchema.INVENTARIO.value}.productos.id_producto", ondelete="CASCADE"),
        primary_key=True
    )
    stock_actual: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )

    # Relación 1:1 inversa con Producto
    producto: Mapped["Producto"] = relationship("Producto", back_populates="inventario")

    def __repr__(self) -> str:
        return f"<Inventario(id_producto={self.id_producto}, stock_actual={self.stock_actual})>"
