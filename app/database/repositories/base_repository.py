"""
Módulo de Repositorio Base Genérico (app/database/repositories/base_repository.py)

Responsabilidad Arquitectónica:
-------------------------------
Implementar el patrón Repository con soporte de tipos genéricos ('Generic[ModelType, IDType]').
Encapsula las consultas SQLAlchemy 2.0 estándar (CRUD) abstrayendo a los servicios de la sintaxis
del ORM.

REGLA CRÍTICA DE DISEÑO:
Los repositorios NUNCA llaman a 'session.commit()'. Su responsabilidad se limita a interactuar
con el contexto de la sesión ('add', 'flush', 'delete', 'select'). La confirmación de la
transacción (commit / rollback) es coordinada exclusivamente por la Capa de Servicios
o el Unit of Work.
"""

from typing import Any, Generic, List, Optional, Sequence, Type, TypeVar
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)
IDType = TypeVar("IDType", bound=Any)


class BaseRepository(Generic[ModelType, IDType]):
    """
    Repositorio base genérico para entidades SQLAlchemy 2.0.
    """

    def __init__(self, model: Type[ModelType], session: Session) -> None:
        self.model = model
        self.session = session

    def get_by_id(self, id_entidad: IDType) -> Optional[ModelType]:
        """Obtiene un registro por su clave primaria."""
        return self.session.get(self.model, id_entidad)

    def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        """Retorna una lista paginada de registros."""
        stmt = select(self.model).offset(skip).limit(limit)
        return self.session.scalars(stmt).all()

    def create(self, entity: ModelType) -> ModelType:
        """
        Agrega la entidad a la sesión y realiza un flush para obtener IDs generados
        sin consolidar el commit final.
        """
        self.session.add(entity)
        self.session.flush()
        self.session.refresh(entity)
        return entity

    def update(self, entity: ModelType) -> ModelType:
        """Sincroniza los cambios de la entidad con la sesión."""
        self.session.flush()
        self.session.refresh(entity)
        return entity

    def delete(self, id_entidad: IDType) -> bool:
        """Elimina físicamente un registro por su ID primario."""
        entity = self.get_by_id(id_entidad)
        if entity is not None:
            self.session.delete(entity)
            self.session.flush()
            return True
        return False
