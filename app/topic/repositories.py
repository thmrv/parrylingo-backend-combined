from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.repositories import BaseRepository
from app.topic.models import Topic
from loggers import get_logger

logger = get_logger(__name__)


class TopicRepository(BaseRepository):
    """Topic repository implementation."""

    def __init__(self):
        super().__init__(Topic)

    async def get_single_by_name(
        self, session: AsyncSession, name: str
    ) -> Topic | None:
        query = (
            select(Topic)
            .where(
                text(
                    """
                    EXISTS (
                        SELECT 1 FROM jsonb_each_text(topic.names) AS kv
                        WHERE TRIM(kv.value) = :name
                    )
                    """
                )
            )
            .params(name=name)
        )

        result = await session.execute(query)
        return result.scalars().first()
