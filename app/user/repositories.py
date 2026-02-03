from typing import List, Sequence
from uuid import UUID

from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.repositories import BaseRepository
from app.lesson.models import Lesson
from app.user.models import (
    Avatar,
    FavoriteUserLesson,
    User,
    UserLessonProgress,
    UserLessonRouletteProgress,
)
from loggers import get_logger

logger = get_logger(__name__)


class UserRepository(BaseRepository):
    """Lesson repository implementation."""

    def __init__(self):
        super().__init__(User)

    async def get_list(self, session: AsyncSession, **filters):
        """Retrieve a paginated list of records using the provided session."""
        # базовый запрос с фильтрами по полям модели
        stmt = select(self.model).filter_by(**filters)
        # добавляем условие email IS NOT NULL
        stmt = stmt.where(self.model.email.isnot(None))
        # сортировка
        stmt = stmt.order_by(self.model.created_at.desc())
        # пагинация
        return await paginate(session, stmt)


class AvatarRepository(BaseRepository):
    """Lesson repository implementation."""

    def __init__(self):
        super().__init__(Avatar)


class FavoriteUserLessonRepository(BaseRepository):
    """Lesson repository implementation."""

    def __init__(self):
        super().__init__(FavoriteUserLesson)

    async def list_user_favorite_lessons(
        self, session: AsyncSession, user_id: UUID
    ) -> Sequence[Lesson]:
        stmt = (
            select(Lesson)
            .join(FavoriteUserLesson, FavoriteUserLesson.lesson_id == Lesson.id)
            .where(FavoriteUserLesson.user_id == user_id)
            .order_by(FavoriteUserLesson.created_at.desc())
        )
        result = await session.execute(stmt)
        return result.unique().scalars().all()


class UserLessonProgressRepository(BaseRepository):
    def __init__(self):
        super().__init__(UserLessonProgress)

    async def list_by_user_and_lessons(
        self,
        session: AsyncSession,
        user_id: UUID,
        language_id: UUID,
        lesson_ids: List[UUID],
    ) -> List[UserLessonProgress]:
        stmt = select(UserLessonProgress).where(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.language_id == language_id,
            UserLessonProgress.lesson_id.in_(lesson_ids),
        )
        result = await session.execute(stmt)
        return result.unique().scalars().all()


class UserLessonRouletteProgressRepository(BaseRepository):
    def __init__(self):
        super().__init__(UserLessonRouletteProgress)
