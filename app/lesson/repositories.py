from typing import Any, List, Optional, Sequence
from uuid import UUID

from sqlalchemy import and_, cast, exists, func, select, update
from sqlalchemy.dialects.postgresql import TEXT, array
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.database.repositories import BaseRepository
from app.lesson.models import Lesson, Word
from app.topic.models import Topic
from app.user.models import FavoriteUserLesson, User
from loggers import get_logger

logger = get_logger(__name__)


class LessonRepository(BaseRepository):
    """Lesson repository implementation."""

    def __init__(self):
        super().__init__(Lesson)

    async def get_list_without_pagination(
        self, session: AsyncSession, **filters
    ) -> List[Lesson]:
        """Retrieve a paginated list of records using the provided session without pagination."""
        query = (
            select(self.model)
            .filter_by(**filters)
            .order_by(self.model.created_at.desc())
        )
        result = await session.execute(query)
        return result.unique().scalars().all()

    async def get_list_without_pagination_new(
        self,
        session: AsyncSession,
        page: int,
        size: int,
        search: Optional[str] = None,
        language_code: Optional[str] = None,
        **filters,
    ) -> tuple[Sequence[Lesson], Any]:
        conditions = []
        if filters.get("is_block") is not None:
            conditions.append(Lesson.is_block == filters["is_block"])
        if filters.get("topic_id") is not None:
            conditions.append(Lesson.topic_id == filters["topic_id"])

        stmt = select(Lesson).where(*conditions)
        
        LANGUAGE_VARIANT_KEYS = {
            "en": ["en_us", "en_gb", "en_ca", "en_au", "en"],
        }
        if search:
            w_search = aliased(Word)
            stmt = stmt.join(w_search, Lesson.id == w_search.lesson_id).where(
                cast(w_search.titles, TEXT).ilike(f"%{search}%")
            )

        if language_code:
            print(f"[DEBUG] Applying JSONB filter for language_code: {language_code}")

            keys_to_check = LANGUAGE_VARIANT_KEYS.get(language_code, [language_code])

            # Use a non-correlated subquery to avoid auto-correlation issues
            word_ids_subq = (
                select(Word.lesson_id)
                .where(
                    Word.titles.op("?|")(array(keys_to_check))
                    & Word.audio_url.op("?|")(array(keys_to_check))
                )
                .group_by(Word.lesson_id)
            )

            stmt = stmt.where(Lesson.id.in_(word_ids_subq))

        else:
            print("[DEBUG] No language_code provided, skipping JSONB filtering")

        total_q = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(total_q)).scalar_one()

        offset = (page - 1) * size
        stmt = stmt.where(Lesson.words.any(Word.media_missing != True)).order_by(Lesson.created_at.desc()).offset(offset).limit(size)

        result = await session.execute(stmt)
        lessons = result.unique().scalars().all()
        return lessons, total

    async def get_latest_lessons_per_author(
        self, session: AsyncSession, search: Optional[str], page: int, size: int
    ) -> tuple[Sequence[Lesson], Any]:
        # 1) Подзапрос: для каждого user_id максимальная дата создания
        subq = (
            select(
                Lesson.user_id.label("uid"),
                func.max(Lesson.updated_at).label("last_dt"),
            )
            .where(Lesson.user_id.isnot(None))
            .where(Lesson.words.any(Word.media_missing != True))
            .group_by(Lesson.user_id)
            .subquery()
        )

        # Алиас для User, чтобы фильтровать по имени
        u = aliased(User)

        # 2) Соединяем Lesson с этим подзапросом
        stmt = (
            select(Lesson)
            .join(
                subq,
                and_(Lesson.user_id == subq.c.uid, Lesson.updated_at == subq.c.last_dt),
            )
            .join(u, Lesson.user_id == u.id)
        )

        # 3) Фильтр по имени автора, если передали search
        if search:
            stmt = stmt.where(u.name.ilike(f"%{search}%"))

        # 4) Считаем общее количество
        count_q = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_q)).scalar_one()

        # 5) Пагинация
        offset = (page - 1) * size
        stmt = stmt.offset(offset).limit(size).order_by(Lesson.updated_at.desc())

        result = await session.execute(stmt)
        lessons = result.unique().scalars().all()
        return lessons, total


class WordRepository(BaseRepository):
    """Lesson repository implementation."""

    def __init__(self, session: AsyncSession = None):
        self.session = session
        super().__init__(Word)

    async def get_all_with_audio(
        self, session: AsyncSession, offset: int
    ) -> Sequence[Word]:
        if offset == 0:
            stmt = select(Word).where(Word.audio_url != None).order_by(Word.updated_at.desc())
        else:
            stmt = select(Word).where(Word.audio_url != None).limit(offset).order_by(Word.updated_at.desc())         
        result = await self.session.execute(stmt)
        return result.unique().scalars().all()

    async def mark_words_as_missing(self, word_ids: list):
        stmt = (
            update(Word)
            .where(Word.id.in_(word_ids))
            .values(media_missing=True)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_random_words(
        self, session: AsyncSession, count: int
    ) -> Sequence[Word]:
        # JOIN по урокам нужного языка и выбираем count случайных
        stmt = (
            select(Word)
            .join(Lesson, Word.lesson_id == Lesson.id)
            .where(Word.media_missing != True)
            .order_by(func.random())
            .limit(count)
        )
        result = await session.execute(stmt)
        return result.unique().scalars().all()
    
    async def get_random_words_by_topic(
        self, session: AsyncSession, count: int, topic_id: str
    ) -> Sequence[Word]:
        if topic_id == None:
            random_topic_subq = (
                select(Topic.id)
                .order_by(func.random())
                .limit(1)
                .scalar_subquery()
            )
            # JOIN по урокам нужного языка и выбираем count случайных
            stmt = (
                select(Word)
                .join(Lesson, Word.lesson_id == Lesson.id)
                .join(Topic, Lesson.topic_id == Topic.id)
                #.where(Lesson.topic_id == random_topic_subq)
                .where(Word.media_missing != True)
                .order_by(func.random())
                .limit(count)
            )
        else:
            stmt = (
                select(Word)
                .join(Lesson, Word.lesson_id == Lesson.id)
                .join(Topic, Lesson.topic_id == Topic.id)
                .where(Lesson.topic_id == topic_id)
                .where(Word.media_missing != True)
                .order_by(func.random())
                .limit(count)
            )
        
        result = await session.execute(stmt)
        return result.unique().scalars().all()

    async def get_random_words_for_user(
        self, session: AsyncSession, user_id: UUID, count: int, topic_id: str
    ) -> Sequence[Word]:
        """
        Случайные слова из всех уроков, которые пользователь добавил в избранное.
        """
        if topic_id == 'null' or topic_id == None:
            stmt = (
                select(Word)
                .join(Lesson, Word.lesson_id == Lesson.id)
                .join(FavoriteUserLesson, FavoriteUserLesson.lesson_id == Lesson.id)
                .where(FavoriteUserLesson.user_id == user_id)
                .where(Word.media_missing != True)
                .order_by(func.random())
                .limit(count)
            )
        else:
            stmt = (
                select(Word)
                .join(Lesson, Word.lesson_id == Lesson.id)
                .join(FavoriteUserLesson, FavoriteUserLesson.lesson_id == Lesson.id)
                .where(Lesson.topic_id == topic_id)
                .where(FavoriteUserLesson.user_id == user_id)
                .where(Word.media_missing != True)
                .order_by(func.random())
                .limit(count)
            )
            
        result = await session.execute(stmt)
        return result.unique().scalars().all()
