"""
Modelo de Producto (app/database/models/inventario/producto.py)

Estructura DDL:
    CREATE TABLE inventario.productos (
        id_producto SERIAL PRIMARY KEY,
        codigo_barras VARCHAR(50) UNIQUE,
        sku VARCHAR(50) UNIQUE,
        nombre VARCHAR(255) NOT NULL,
        descripcion TEXT,
        id_categoria INT REFERENCES inventario.categorias(id_categoria),
        id_marca INT REFERENCES inventario.marcas(id_marca),
        id_unidad INT REFERENCES inventario.unidades(id_unidad),
        precio_compra DECIMAL(12,2) CHECK (precio_compra >= 0) NOT NULL,
        precio_venta DECIMAL(12,2) CHECK (precio_venta >= 0) NOT NULL,
        stock_minimo INT CHECK (stock_minimo >= 0),
        activo BOOLEAN DEFAULT TRUE,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
        fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DatabaseSchema
from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.inventario.categoria import Categoria
    from app.database.models.inventario.marca import Marca
    from app.database.models.inventario.unidad import Unidad
    from app.database.models.inventario.inventario import Inventario
    from app.database.models.inventario.movimiento_inventario import MovimientoInventario
    from app.database.models.compras.compra import DetalleCompra
    from app.database.models.ventas.venta import DetalleVenta


class Producto(Base):
    """
    Catálogo de productos en el esquema 'inventario'.
    """
    __tablename__ = "productos"
    __table_args__ = (
        CheckConstraint("precio_compra >= 0", name="chk_precio_compra_positivo"),
        CheckConstraint("precio_venta >= 0", name="chk_precio_venta_positivo"),
        CheckConstraint("stock_minimo >= 0", name="chk_stock_minimo_positivo"),
        {"schema": DatabaseSchema.INVENTARIO.value}
    )

    id_producto: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_barras: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True, nullable=True)
    sku: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True, nullable=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Llaves foráneas
    id_categoria: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey(f"{DatabaseSchema.INVENTARIO.value}.categorias.id_categoria"),
        nullable=True
    )
    id_marca: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey(f"{DatabaseSchema.INVENTARIO.value}.marcas.id_marca"),
        nullable=True
    )
    id_unidad: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey(f"{DatabaseSchema.INVENTARIO.value}.unidades.id_unidad"),
        nullable=True
    )

    # Precios y stock
    precio_compra: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    precio_venta: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    stock_minimo: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)

    # Estado y Auditoría
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )
    fecha_modificacion: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )

    # Relaciones ORM
    categoria: Mapped[Optional["Categoria"]] = relationship("Categoria", back_populates="productos")
    marca: Mapped[Optional["Marca"]] = relationship("Marca", back_populates="productos")
    unidad: Mapped[Optional["Unidad"]] = relationship("Unidad", back_populates="productos")
    
    # 1 a 1 con inventario
    inventario: Mapped[Optional["Inventario"]] = relationship(
        "Inventario", back_populates="producto", uselist=False, cascade="all, delete-orphan"
    )
    # 1 a N con movimientos
    movimientos: Mapped[List["MovimientoInventario"]] = relationship(
        "MovimientoInventario", back_populates="producto"
    )
    detalles_compra: Mapped[List["DetalleCompra"]] = relationship(
        "DetalleCompra", back_populates="producto"
    )
    detalles_venta: Mapped[List["DetalleVenta"]] = relationship(
        "DetalleVenta", back_populates="producto"
    )

    def __repr__(self) -> str:
        return f"<Producto(id_producto={self.id_producto}, sku='{self.sku}', nombre='{self.nombre}')>"
