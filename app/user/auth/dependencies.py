from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database_async import get_session
from app.core.settings import settings
from app.user.dependencies import get_user_service
from app.user.models import User

access_token_header = APIKeyHeader(
    name="Authorization", scheme_name="access-token", auto_error=False
)
refresh_token_header = APIKeyHeader(name="Authorization", scheme_name="refresh-token")


async def get_current_user_optional(
    token: str = Security(access_token_header),  # тот же header
    session: AsyncSession = Depends(get_session),
) -> Optional[User]:
    if not token:
        return None
    try:
        return await get_current_user(token=token, session=session)
    except HTTPException:
        return None


async def get_current_user(
    token: str = Security(access_token_header),
    session: AsyncSession = Depends(get_session),
) -> User:
    if not token:  # если заголовок вообще не пришёл
        raise HTTPException(status_code=401, detail="Not authenticated")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        payload = jwt.decode(
            token, settings.jwt_user_secret_key, algorithms=[settings.algorithm]
        )
        id = payload.get("sub")
        mode = payload.get("mode")

        if id is None or mode != "access_token":
            raise credentials_exception

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has been expired")

    except jwt.InvalidTokenError:
        raise credentials_exception

    user = await get_user_service().get_single(session, id=id)
    if not user:
        raise credentials_exception

    return user


async def get_access_by_refresh_token(
    refresh_token: str = Security(refresh_token_header),
    session: AsyncSession = Depends(get_session),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        payload = jwt.decode(
            refresh_token,
            settings.jwt_user_secret_key,
            algorithms=[settings.algorithm],
        )
        id = payload.get("sub")
        mode = payload.get("mode")

        if id is None or mode != "refresh_token":
            raise credentials_exception

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has been expired")

    except jwt.InvalidTokenError:
        raise credentials_exception

    user = await get_user_service().get_single(session, id=id)
    if not user:
        raise credentials_exception

    return user
