from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database_async import get_session
from app.user.auth.dependencies import get_access_by_refresh_token
from app.user.auth.schemas import TokenModel, TokenRefreshModel
from app.user.auth.security import create_access_token
from app.user.dependencies import get_user_service
from app.user.models import User
from app.user.schemas import CreateUserModel, LoginUserModel, UserProfileViewModel
from app.user.services import UserService

router = APIRouter()


@router.post("/signup", status_code=201, response_model=UserProfileViewModel)
async def signup_user(
    user_form_data: CreateUserModel,
    background_tasks: BackgroundTasks,
    user_service: Annotated[UserService, Depends(get_user_service)],
    session: AsyncSession = Depends(get_session),
) -> UserProfileViewModel:
    """
    Create a new user account.
    """
    return await user_service.create_user_and_send_info_to_email(
        session=session, data=user_form_data, background_tasks=background_tasks
    )


@router.post("/login", response_model=TokenModel)
async def login_user(
    login_form_data: LoginUserModel,
    user_service: Annotated[UserService, Depends(get_user_service)],
    session: AsyncSession = Depends(get_session),
) -> TokenModel:
    """
    Authenticate user and return tokens.
    """
    return await user_service.authenticate_user(session, data=login_form_data)


@router.post("/login/refresh", response_model=TokenRefreshModel)
async def get_access_by_refresh(
    current_user: Annotated[User, Depends(get_access_by_refresh_token)]
) -> TokenRefreshModel:
    """
    Refresh the access token using a valid refresh token.
    """
    return TokenRefreshModel(
        access_token=create_access_token({"sub": str(current_user.id)})
    )
