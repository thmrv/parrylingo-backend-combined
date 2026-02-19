from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.repositories import BaseRepository
from app.topic.models import Topic
from loggers import get_logger
from typing import List

from pyuca import Collator
import unicodedata

from fastapi.responses import HTMLResponse

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
    RE_NON_PRINTABLE = re.compile(r'[\x00-\x1f\x7f-\x9f\xad\u200b-\u200d\ufeff]')

    def topic_sort_key(topic):
        name = topic.names.get("en", "")
        print(f"Hex: {name.encode('utf-16').hex()}")
        print(f"Ordinals: {[ord(c) for c in name]}")
        
        names_dict = topic.names or {}
        raw_val = next(iter(names_dict.values()), "")
    
        clean_str = RE_NON_PRINTABLE.sub('', str(raw_val))

        clean_str = clean_str.strip()

        processed_str = unicodedata.normalize('NFKD', clean_str).casefold()

        if not processed_str:
            return [float('inf')] 
        
        return collator.sort_key(processed_str)

    topics = result.scalars().unique().all()
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
