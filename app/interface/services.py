from app.core.services import BaseService
from app.interface.repositories import InterfaceRepository
from loggers import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class InterfaceService(BaseService):

    def __init__(self, repository: InterfaceRepository):
        super().__init__(repository)
        self.repository = repository

    def delete(self, session: AsyncSession, language_code: str):
        return self.repository.delete(session = session, language_code = language_code)
        