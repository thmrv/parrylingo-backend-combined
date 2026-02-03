from typing import List, Optional, Type, TypeVar

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from loggers import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class BaseRepository:
    """Base repository with common SQLAlchemy operations using context-managed sessions."""

    def __init__(self, model: Type[T]):
        self.model = model

    async def create(
        self, session: AsyncSession, data: dict, commit: bool = True
    ) -> Optional[T]:
        """Create a new record using the provided session."""
        try:
            instance = self.model(**data)
            session.add(instance)
            if commit:
                await session.commit()
                await session.refresh(instance)
            logger.info("%s created successfully.", self.model.__name__)
            return instance
        except (IntegrityError, SQLAlchemyError):
            if commit:
                await session.rollback()
            raise

    async def get_single(self, session: AsyncSession, **filters) -> Optional[T]:
        """Retrieve a single record using the provided session."""
        query = select(self.model).filter_by(**filters)
        result = await session.execute(query)
        return result.scalars().first()

    async def get_list(self, session: AsyncSession, **filters) -> Page[T]:
        """Retrieve a paginated list of records using the provided session."""
        query = (
            select(self.model)
            .filter_by(**filters)
            .order_by(self.model.created_at.desc())
        )
        return await paginate(session, query)

    async def get_list_without_pagination(
        self, session: AsyncSession, **filters
    ) -> List[T]:
        """Retrieve a paginated list of records using the provided session without pagination."""
        query = (
            select(self.model)
            .filter_by(**filters)
            .order_by(self.model.created_at.desc())
        )
        result = await session.execute(query)
        return result.scalars().all()

    async def update(
        self, session: AsyncSession, data: dict, commit: bool = True, **filters
    ) -> Optional[T]:
        """Update a record using the provided session."""
        try:
            query = select(self.model).filter_by(**filters)
            result = await session.execute(query)
            instance = result.scalars().first()
            if instance:
                for key, value in data.items():
                    setattr(instance, key, value)
                if commit:
                    await session.commit()
                    await session.refresh(instance)
                logger.info("%s updated successfully.", self.model.__name__)
                return instance
            return None
        except (IntegrityError, SQLAlchemyError):
            if commit:
                await session.rollback()
            raise

    async def delete(
        self, session: AsyncSession, commit: bool = True, **filters
    ) -> Optional[T]:
        """Delete a record using the provided session."""
        try:
            query = select(self.model).filter_by(**filters)
            result = await session.execute(query)
            instance = result.scalars().first()
            if instance:
                if commit:
                    await session.delete(instance)
                    await session.commit()
                logger.info("%s deleted successfully.", self.model.__name__)
                return instance
            return None
        except (IntegrityError, SQLAlchemyError):
            if commit:
                await session.rollback()
            raise
