"""
Modelos de Compra y Detalle de Compras (app/database/models/compras/compra.py)

Estructura DDL:
    CREATE TABLE compras.compras (
        id_compra SERIAL PRIMARY KEY,
        id_proveedor INT NOT NULL,
        fecha_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        subtotal DECIMAL(12,2) DEFAULT 0.00,
        impuestos DECIMAL(12,2) DEFAULT 0.00,
        total DECIMAL(12,2) DEFAULT 0.00,
        estado VARCHAR(20) DEFAULT 'PENDIENTE',
        id_usuario INT NOT NULL,
        CONSTRAINT fk_compras_proveedor FOREIGN KEY (id_proveedor) REFERENCES compras.proveedores(id_proveedor) ON DELETE RESTRICT,
        CONSTRAINT fk_compras_usuario FOREIGN KEY (id_usuario) REFERENCES seguridad.usuarios(id_usuario) ON DELETE RESTRICT,
        CONSTRAINT chk_estado_compras CHECK (estado IN ('PENDIENTE', 'COMPLETADA', 'ANULADA'))
    );

    CREATE TABLE compras.detalle_compras (
        id_detalle SERIAL PRIMARY KEY,
        id_compra INT REFERENCES compras.compras(id_compra) ON DELETE CASCADE,
        id_producto INT REFERENCES inventario.productos(id_producto) ON DELETE RESTRICT,
        cantidad INT NOT NULL,
        costo_unitario NUMERIC(12,2) NOT NULL,
        subtotal NUMERIC(12,2) NOT NULL
    );
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List
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
    from app.database.models.compras.proveedor import Proveedor
    from app.database.models.seguridad.usuario import Usuario
    from app.database.models.inventario.producto import Producto


class Compra(Base):
    """
    Cabecera de compras en el esquema 'compras'.
    """
    __tablename__ = "compras"
    __table_args__ = (
        CheckConstraint("estado IN ('PENDIENTE', 'COMPLETADA', 'ANULADA')", name="chk_estado_compras"),
        {"schema": DatabaseSchema.COMPRAS.value}
    )

    id_compra: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_proveedor: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(f"{DatabaseSchema.COMPRAS.value}.proveedores.id_proveedor", ondelete="RESTRICT"),
        nullable=False, index=True
    )
    fecha_compra: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    impuestos: Mapped[Decimal] = mapped_column(
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
    proveedor: Mapped["Proveedor"] = relationship("Proveedor", back_populates="compras")
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="compras")
    detalles: Mapped[List["DetalleCompra"]] = relationship(
        "DetalleCompra", back_populates="compra", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Compra(id_compra={self.id_compra}, total={self.total}, estado='{self.estado}')>"


class DetalleCompra(Base):
    """
    Detalle de productos comprados en la tabla 'compras.detalle_compras'.
    """
    __tablename__ = "detalle_compras"
    __table_args__ = {"schema": DatabaseSchema.COMPRAS.value}

    id_detalle: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_compra: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(f"{DatabaseSchema.COMPRAS.value}.compras.id_compra", ondelete="CASCADE"),
        nullable=False, index=True
    )
    id_producto: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(f"{DatabaseSchema.INVENTARIO.value}.productos.id_producto", ondelete="RESTRICT"),
        nullable=False, index=True
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    costo_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Relaciones
    compra: Mapped["Compra"] = relationship("Compra", back_populates="detalles")
    producto: Mapped["Producto"] = relationship("Producto", back_populates="detalles_compra")

    def __repr__(self) -> str:
        return f"<DetalleCompra(id_detalle={self.id_detalle}, compra={self.id_compra}, cant={self.cantidad})>"
