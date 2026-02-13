from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services import BaseService
from app.language.repositories import LanguageRepository
from loggers import get_logger

logger = get_logger(__name__)


class LanguageService(BaseService):

    def __init__(self, repository: LanguageRepository):
        super().__init__(repository)

    async def get_list_without_pagination(
        self, session: AsyncSession, with_lessons: bool = False, with_flags: bool = False
    ):
        return await self.repository.get_list_without_pagination(
            session, with_lessons=with_lessons, with_flags=with_flags
        )
