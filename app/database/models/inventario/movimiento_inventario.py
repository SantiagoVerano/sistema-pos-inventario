"""
Modelo de Movimientos de Inventario (app/database/models/inventario/movimiento_inventario.py)

Estructura DDL:
    CREATE TABLE inventario.movimientos_inventario (
        id_movimiento SERIAL PRIMARY KEY,
        id_producto INT REFERENCES inventario.productos(id_producto) ON DELETE RESTRICT,
        tipo_movimiento VARCHAR(20) NOT NULL 
            CHECK (tipo_movimiento IN ('ENTRADA', 'SALIDA', 'AJUSTE', 'DEVOLUCION')),
        cantidad INT NOT NULL,
        referencia VARCHAR(100),
        observacion TEXT,
        id_usuario INT REFERENCES seguridad.usuarios(id_usuario) ON DELETE RESTRICT,
        fecha_movimiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DatabaseSchema
from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.inventario.producto import Producto
    from app.database.models.seguridad.usuario import Usuario


class MovimientoInventario(Base):
    """
    Kardex de movimientos en el esquema 'inventario'.
    """
    __tablename__ = "movimientos_inventario"
    __table_args__ = (
        CheckConstraint(
            "tipo_movimiento IN ('ENTRADA', 'SALIDA', 'AJUSTE', 'DEVOLUCION')",
            name="chk_tipo_movimiento"
        ),
        {"schema": DatabaseSchema.INVENTARIO.value}
    )

    id_movimiento: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_producto: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(f"{DatabaseSchema.INVENTARIO.value}.productos.id_producto", ondelete="RESTRICT"),
        nullable=False, index=True
    )
    tipo_movimiento: Mapped[str] = mapped_column(String(20), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    referencia: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    observacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    id_usuario: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(f"{DatabaseSchema.SEGURIDAD.value}.usuarios.id_usuario", ondelete="RESTRICT"),
        nullable=False, index=True
    )
    fecha_movimiento: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )

    # Relaciones
    producto: Mapped["Producto"] = relationship("Producto", back_populates="movimientos")
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="movimientos_inventario")

    def __repr__(self) -> str:
        return (
            f"<MovimientoInventario(id={self.id_movimiento}, producto={self.id_producto}, "
            f"tipo='{self.tipo_movimiento}', cant={self.cantidad})>"
        )
