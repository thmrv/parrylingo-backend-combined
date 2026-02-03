from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.auth.dependencies import (
    get_access_by_refresh_token,
    get_current_superuser,
)
from app.admin.auth.schemas import TokenModel, TokenRefreshModel
from app.admin.auth.security import create_access_token
from app.admin.dependencies import get_superuser_service
from app.admin.models import SuperUser
from app.admin.schemas import LoginSuperUserSchema, SuperUserProfileViewModel
from app.admin.services import SuperUserService
from app.core.database.database_async import get_session

router = APIRouter(prefix="/auth")


@router.post("/login/", response_model=TokenModel)
async def login_superuser(
    login_form_data: LoginSuperUserSchema,
    superuser_service: Annotated[SuperUserService, Depends(get_superuser_service)],
    session: AsyncSession = Depends(get_session),
) -> TokenModel:
    """
    Authenticate user and return tokens.
    """
    auth_token = await superuser_service.authenticate_superuser(
        session, login_form_data
    )
    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    return auth_token


@router.post("/login/refresh/", response_model=TokenRefreshModel)
async def get_access_by_refresh(
    current_superuser: Annotated[SuperUser, Depends(get_access_by_refresh_token)],
) -> TokenRefreshModel:
    """
    Refresh the access token using a valid refresh token.
    """
    return TokenRefreshModel(
        access_token=create_access_token({"sub": str(current_superuser.id)})
    )


@router.get("/profile/", response_model=SuperUserProfileViewModel)
async def get_superuser_profile(
    current_superuser: Annotated[SuperUser, Depends(get_current_superuser)],
):
    """
    Returns the current superuser profile.
    """
    return current_superuser
