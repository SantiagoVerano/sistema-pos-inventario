"""
Repositorio de Usuarios (app/database/repositories/seguridad/usuario_repository.py)

Responsabilidad Arquitectónica:
-------------------------------
Gestionar las operaciones de persistencia y consultas de la entidad Usuario y la tabla
intermedia usuario_rol en el esquema 'seguridad'.
"""

from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database.models.seguridad.usuario import Usuario
from app.database.models.seguridad.rol import Rol, UsuarioRol
from app.database.repositories.base_repository import BaseRepository


class UsuarioRepository(BaseRepository[Usuario, int]):
    """
    Repositorio para la entidad Usuario.
    """

    def __init__(self, session: Session) -> None:
        super().__init__(Usuario, session)

    def obtener_por_id(self, id_usuario: int) -> Optional[Usuario]:
        """Obtiene un usuario por su clave primaria con roles pre-cargados."""
        stmt = (
            select(Usuario)
            .options(joinedload(Usuario.roles_asociados).joinedload(UsuarioRol.rol))
            .where(Usuario.id_usuario == id_usuario)
        )
        return self.session.scalars(stmt).unique().first()

    def obtener_por_correo(self, correo: str) -> Optional[Usuario]:
        """Busca un usuario por su correo electrónico único."""
        stmt = (
            select(Usuario)
            .options(joinedload(Usuario.roles_asociados).joinedload(UsuarioRol.rol))
            .where(Usuario.correo == correo.strip().lower())
        )
        return self.session.scalars(stmt).unique().first()

    def listar_activos(self) -> Sequence[Usuario]:
        """Retorna todos los usuarios que tienen el estado activo = True."""
        stmt = (
            select(Usuario)
            .options(joinedload(Usuario.roles_asociados).joinedload(UsuarioRol.rol))
            .where(Usuario.activo.is_(True))
            .order_by(Usuario.nombre.asc())
        )
        return self.session.scalars(stmt).unique().all()

    def asignar_rol(self, id_usuario: int, id_rol: int) -> UsuarioRol:
        """Asocia un rol a un usuario en la tabla seguridad.usuario_rol."""
        # Verificar si ya existe la asociación
        stmt = select(UsuarioRol).where(
            UsuarioRol.id_usuario == id_usuario,
            UsuarioRol.id_rol == id_rol
        )
        existente = self.session.scalars(stmt).first()
        if existente:
            return existente

        usuario_rol = UsuarioRol(id_usuario=id_usuario, id_rol=id_rol)
        self.session.add(usuario_rol)
        self.session.flush()
        return usuario_rol

    def remover_rol(self, id_usuario: int, id_rol: int) -> bool:
        """Remueve la asignación de un rol a un usuario."""
        stmt = select(UsuarioRol).where(
            UsuarioRol.id_usuario == id_usuario,
            UsuarioRol.id_rol == id_rol
        )
        relacion = self.session.scalars(stmt).first()
        if relacion:
            self.session.delete(relacion)
            self.session.flush()
            return True
        return False

    def obtener_roles_usuario(self, id_usuario: int) -> Sequence[Rol]:
        """Obtiene la lista de roles asignados a un usuario."""
        stmt = (
            select(Rol)
            .join(UsuarioRol, Rol.id_rol == UsuarioRol.id_rol)
            .where(UsuarioRol.id_usuario == id_usuario)
        )
        return self.session.scalars(stmt).all()

    def cambiar_estado_activo(self, id_usuario: int, activo: bool) -> Optional[Usuario]:
        """Habilita o deshabilita la cuenta de un usuario."""
        usuario = self.get_by_id(id_usuario)
        if usuario:
            usuario.activo = activo
            self.session.flush()
            self.session.refresh(usuario)
        return usuario
