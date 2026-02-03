import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependencies import get_superuser_service
from app.admin.models import SuperUser
from app.core.database.database_async import get_session
from app.core.settings import settings
from loggers import get_logger

logger = get_logger(__name__)

access_token_header = APIKeyHeader(name="Authorization", scheme_name="access-token")
refresh_token_header = APIKeyHeader(name="Authorization", scheme_name="refresh-token")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="could not validate credentials",
)
token_expired_exception = HTTPException(
    status_code=403, detail="token has been expired"
)


async def get_current_superuser(
    token: str = Security(access_token_header),
    session: AsyncSession = Depends(get_session),
) -> SuperUser:
    try:
        payload = jwt.decode(
            token, settings.jwt_superuser_secret_key, algorithms=[settings.algorithm]
        )
        id = payload.get("sub")
        mode = payload.get("mode")
        if id is None or mode != "access_token":
            raise credentials_exception

    except jwt.ExpiredSignatureError:
        raise token_expired_exception

    except jwt.InvalidTokenError:
        raise credentials_exception

    super_user_service = get_superuser_service()
    superuser = await super_user_service.get_single(session, id=id)
    if not superuser:
        raise credentials_exception

    return superuser


async def get_access_by_refresh_token(
    refresh_token: str = Security(refresh_token_header),
    session: AsyncSession = Depends(get_session),
) -> SuperUser:
    try:
        payload = jwt.decode(
            refresh_token,
            settings.jwt_superuser_secret_key,
            algorithms=[settings.algorithm],
        )
        id = payload.get("sub")
        mode = payload.get("mode")

        if id is None or mode != "refresh_token":
            raise credentials_exception

    except jwt.ExpiredSignatureError:
        raise token_expired_exception

    except jwt.InvalidTokenError:
        raise credentials_exception

    super_user_service = get_superuser_service()
    superuser = await super_user_service.get_single(session, id=id)
    if not superuser:
        raise credentials_exception

    return superuser
