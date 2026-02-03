from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.models import SuperUser
from app.core.database.repositories import BaseRepository
from loggers import get_logger

logger = get_logger(__name__)


class SuperUserRepository(BaseRepository):
    """
    User repository
    """

    def __init__(self):
        super().__init__(SuperUser)

    async def update_password(
        self, session: AsyncSession, user_id: UUID, new_password: str
    ) -> bool:
        result = await session.execute(select(SuperUser).where(SuperUser.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            logger.warning("SuperUser with ID %s not found", user_id)
            return False

        user.password = new_password
        await session.commit()
        logger.info("Password updated for SuperUser ID: %s", user_id)
        return True
