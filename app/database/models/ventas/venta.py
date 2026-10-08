"""
Modelos de Venta y Detalle de Venta (app/database/models/ventas/venta.py)

Estructura DDL:
    CREATE TABLE ventas.ventas (
        id_venta SERIAL PRIMARY KEY,
        id_cliente INT REFERENCES ventas.clientes(id_cliente) ON DELETE RESTRICT,
        fecha_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        subtotal NUMERIC(12,2) NOT NULL DEFAULT 0.00,
        impuestos NUMERIC(12,2) NOT NULL DEFAULT 0.00,
        descuento NUMERIC(12,2) NOT NULL DEFAULT 0.00,
        total NUMERIC(12,2) NOT NULL DEFAULT 0.00,
        estado VARCHAR(20) DEFAULT 'PENDIENTE',
        id_usuario INT REFERENCES seguridad.usuarios(id_usuario) ON DELETE RESTRICT,
        CONSTRAINT chk_estado_ventas CHECK (estado IN ('PENDIENTE', 'COMPLETADA', 'ANULADA'))
    );

    CREATE TABLE ventas.detalle_venta ( 
        id_detalle SERIAL PRIMARY KEY,
        id_venta INT REFERENCES ventas.ventas(id_venta) ON DELETE CASCADE,
        id_producto INT REFERENCES inventario.productos(id_producto) ON DELETE RESTRICT,
        cantidad INT NOT NULL,
        precio_unitario NUMERIC(12,2) NOT NULL,
        subtotal NUMERIC(12,2) NOT NULL
    );
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DatabaseSchema
from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.ventas.cliente import Cliente
    from app.database.models.seguridad.usuario import Usuario
    from app.database.models.inventario.producto import Producto


class Venta(Base):
    """
    Cabecera de ventas en el esquema 'ventas'.
    """
    __tablename__ = "ventas"
    __table_args__ = (
        CheckConstraint("estado IN ('PENDIENTE', 'COMPLETADA', 'ANULADA')", name="chk_estado_ventas"),
        {"schema": DatabaseSchema.VENTAS.value}
    )

    id_venta: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_cliente: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey(f"{DatabaseSchema.VENTAS.value}.clientes.id_cliente", ondelete="RESTRICT"),
        nullable=True, index=True
    )
    fecha_venta: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False, index=True
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    impuestos: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    descuento: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    estado: Mapped[str] = mapped_column(
        String(20), default="PENDIENTE", nullable=False
    )
    id_usuario: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(f"{DatabaseSchema.SEGURIDAD.value}.usuarios.id_usuario", ondelete="RESTRICT"),
        nullable=False, index=True
    )

    # Relaciones
    cliente: Mapped[Optional["Cliente"]] = relationship("Cliente", back_populates="ventas")
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="ventas")
    detalles: Mapped[List["DetalleVenta"]] = relationship(
        "DetalleVenta", back_populates="venta", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Venta(id_venta={self.id_venta}, total={self.total}, estado='{self.estado}')>"


class DetalleVenta(Base):
    """
    Detalle de productos vendidos en la tabla 'ventas.detalle_venta'.
    """
    __tablename__ = "detalle_venta"
    __table_args__ = {"schema": DatabaseSchema.VENTAS.value}

    id_detalle: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_venta: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(f"{DatabaseSchema.VENTAS.value}.ventas.id_venta", ondelete="CASCADE"),
        nullable=False, index=True
    )
    id_producto: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(f"{DatabaseSchema.INVENTARIO.value}.productos.id_producto", ondelete="RESTRICT"),
        nullable=False, index=True
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Relaciones
    venta: Mapped["Venta"] = relationship("Venta", back_populates="detalles")
    producto: Mapped["Producto"] = relationship("Producto", back_populates="detalles_venta")

    def __repr__(self) -> str:
        return f"<DetalleVenta(id_detalle={self.id_detalle}, venta={self.id_venta}, cant={self.cantidad})>"
