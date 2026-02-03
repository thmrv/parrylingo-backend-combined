from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.auth.schemas import TokenModel
from app.admin.auth.security import create_access_token, create_refresh_token
from app.admin.repositories import SuperUserRepository
from app.admin.schemas import LoginSuperUserSchema
from app.core.services import BaseService
from app.core.utils import verify_password
from loggers import get_logger

logger = get_logger(__name__)


class SuperUserService(BaseService):
    def __init__(self, repository: SuperUserRepository):
        super().__init__(repository)

    async def authenticate_superuser(
        self, session: AsyncSession, data: LoginSuperUserSchema
    ) -> TokenModel | bool:
        superuser = await self.repository.get_single(session, login=data.login)
        if not superuser:
            return False

        if not verify_password(data.password, superuser.password):
            return False

        data = {"sub": str(superuser.id)}

        return TokenModel(
            access_token=create_access_token(data),
            refresh_token=create_refresh_token(data),
        )
