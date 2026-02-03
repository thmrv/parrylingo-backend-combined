from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services import BaseService
from app.topic.models import Topic
from app.topic.repositories import TopicRepository


class TopicService(BaseService):

    def __init__(
        self,
        repository: TopicRepository,
    ):
        super().__init__(repository)

    async def get_single_by_name(self, session: AsyncSession, name: str) -> Topic:
        return await self.repository.get_single_by_name(session, name)
