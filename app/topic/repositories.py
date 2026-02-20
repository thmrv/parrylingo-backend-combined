from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.repositories import BaseRepository
from app.topic.models import Topic
from loggers import get_logger

from typing import List
from pyuca import Collator
import unicodedata

logger = get_logger(__name__)

class TopicRepository(BaseRepository):
    """Topic repository implementation."""

    def __init__(self):
        super().__init__(Topic)

    async def get_list_without_pagination(
        self, session: AsyncSession, **filters
    ) -> List[Topic]:
        query = select(self.model).filter_by(**filters)
        result = await session.execute(query)
        topics = result.scalars().unique().all()

        collator = Collator()
        
        def topic_sort_key(topic):
            names_dict = topic.names['ru'] or ''
            #raw_val = next(iter(names_dict.values()), "")
    
            clean_name = unicodedata.normalize('NFKD', str(names_dict).strip()).casefold()
    
            return collator.sort_key(clean_name)
        
        return sorted(topics, key=topic_sort_key)

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
