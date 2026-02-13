from typing import List

from sqlalchemy import select, join
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.repositories import BaseRepository
from app.language.models import Language
from loggers import get_logger

from app.interface.models import Interface

logger = get_logger(__name__)


class LanguageRepository(BaseRepository):
    """Lesson repository implementation."""

    def __init__(self):
        super().__init__(Language)

    async def get_list_without_pagination(
        self, session: AsyncSession, with_lessons: bool = False, with_flags: bool = False, **filters
    ) -> List[Language]:
        query = select(self.model).withfilter_by(**filters)
        
        if with_flags:
            query = select(Language, Interface).join(Interface, Language.language_code == Interface.language_code).withfilter_by(**filters)
            
        # if with_lessons:
        #     lesson_exists_subq = exists().where(self.model.id == Lesson.language_id)
        #     query = query.filter(lesson_exists_subq)

        query = query.order_by(self.model.created_at.desc())
        result = await session.execute(query)
        return result.scalars().all()
