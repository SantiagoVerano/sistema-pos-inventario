"""
Módulo de Base Declarativa y Mixins Reutilizables (app/database/base.py)

Responsabilidad Arquitectónica:
-------------------------------
Define la clase base declarativa de SQLAlchemy 2.0 ('Base') y mixins modulares
para estandarizar columnas comunes (marcas de tiempo, auditoría de usuario y estado activo)
en todas las entidades de los 4 esquemas de la base de datos PostgreSQL.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Clase base declarativa moderna de SQLAlchemy 2.0.
    Todos los modelos del sistema heredan de esta clase.
    """
    pass


class TimestampMixin:
    """
    Mixin para registrar automáticamente la fecha y hora de creación y
    última modificación a nivel de base de datos PostgreSQL.
    """
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Fecha y hora de inserción del registro en la BD"
    )
    fecha_modificacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Fecha y hora de la última actualización del registro"
    )


class AuditMixin:
    """
    Mixin para registrar qué usuario fue el autor de la creación o modificación
    del registro (apunta al esquema seguridad.usuarios).
    """
    id_usuario_creacion: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("seguridad.usuarios.id_usuario", ondelete="SET NULL"),
        nullable=True,
        comment="ID del usuario que creó el registro"
    )
    id_usuario_modificacion: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("seguridad.usuarios.id_usuario", ondelete="SET NULL"),
        nullable=True,
        comment="ID del último usuario que modificó el registro"
    )


class ActivoMixin:
    """
    Mixin para implementar borrado lógico o deshabilitación de registros
    sin eliminar físicamente filas de la base de datos.
    """
    activo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Indica si el registro está activo y disponible para operaciones"
    )
