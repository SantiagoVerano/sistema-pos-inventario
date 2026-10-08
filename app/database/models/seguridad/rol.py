"""
Modelos de Roles y UsuarioRol (app/database/models/seguridad/rol.py)

Estructura DDL:
    CREATE TABLE seguridad.roles (
        id_rol SERIAL PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL UNIQUE
    );

    CREATE TABLE seguridad.usuario_rol (
        id_usuario INT NOT NULL,
        id_rol INT NOT NULL,
        PRIMARY KEY (id_usuario, id_rol),
        CONSTRAINT fk_usuariorol_usuario FOREIGN KEY (id_usuario) REFERENCES seguridad.usuarios(id_usuario) ON DELETE CASCADE,
        CONSTRAINT fk_usuariorol_rol FOREIGN KEY (id_rol) REFERENCES seguridad.roles(id_rol) ON DELETE RESTRICT
    );
"""

from typing import TYPE_CHECKING, List
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DatabaseSchema
from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.seguridad.usuario import Usuario


class Rol(Base):
    """
    Catálogo de roles en el esquema 'seguridad'.
    """
    __tablename__ = "roles"
    __table_args__ = {"schema": DatabaseSchema.SEGURIDAD.value}

    id_rol: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)

    # Relaciones
    usuarios_asociados: Mapped[List["UsuarioRol"]] = relationship(
        "UsuarioRol", back_populates="rol", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Rol(id_rol={self.id_rol}, nombre='{self.nombre}')>"


class UsuarioRol(Base):
    """
    Tabla intermedia 'seguridad.usuario_rol' con clave primaria compuesta (id_usuario, id_rol).
    """
    __tablename__ = "usuario_rol"
    __table_args__ = {"schema": DatabaseSchema.SEGURIDAD.value}

    id_usuario: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(f"{DatabaseSchema.SEGURIDAD.value}.usuarios.id_usuario", ondelete="CASCADE"),
        primary_key=True,
    )
    id_rol: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(f"{DatabaseSchema.SEGURIDAD.value}.roles.id_rol", ondelete="RESTRICT"),
        primary_key=True,
    )

    # Relaciones ORM
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="roles_asociados")
    rol: Mapped["Rol"] = relationship("Rol", back_populates="usuarios_asociados")

    def __repr__(self) -> str:
        return f"<UsuarioRol(id_usuario={self.id_usuario}, id_rol={self.id_rol})>"
