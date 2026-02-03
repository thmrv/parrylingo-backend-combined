from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi_pagination import Page
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database_async import get_session
from app.user.auth.dependencies import get_current_user
from app.user.dependencies import get_avatar_service, get_user_service
from app.user.models import User as UserModel
from app.user.schemas import (
    AvatarSchema,
    ProfileUpdate,
    UserBlockShema,
    UserProfileViewModel,
)
from app.user.services import AvatarService, UserService

router = APIRouter(prefix="/user")
admin_router = APIRouter(prefix="/admin")


@router.get("/profile", response_model=UserProfileViewModel)
async def get_profile(
    current_user: UserModel = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
    session: AsyncSession = Depends(get_session),
):
    profile = await service.get_single(session, id=current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return profile


@router.get("/admin/users", response_model=Page[UserProfileViewModel])
async def get_users(
    service: UserService = Depends(get_user_service),
    session: AsyncSession = Depends(get_session),
):
    return await service.get_list(session)


@router.post("/admin/block-user/{user_id}", response_model=UserProfileViewModel)
async def block_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
    session: AsyncSession = Depends(get_session),
):
    data = UserBlockShema(is_block=True)
    return await service.update(session, data, id=user_id)


@router.delete("/admin/unblock-user/{user_id}", response_model=UserProfileViewModel)
async def unblock_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
    session: AsyncSession = Depends(get_session),
):
    data = UserBlockShema(is_block=False)
    return await service.update(session, data, id=user_id)


@router.patch("/profile", response_model=UserProfileViewModel)
async def update_profile(
    data: ProfileUpdate,
    current_user: UserModel = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
    session: AsyncSession = Depends(get_session),
):
    updated = await service.update(
        session,
        data=data,
        id=current_user.id,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return updated


@admin_router.post("/avatar", response_model=AvatarSchema)
async def create_avatar(
    avatar: UploadFile = File(...),
    service: AvatarService = Depends(get_avatar_service),
    session: AsyncSession = Depends(get_session),
):
    return await service.create(session, avatar=avatar)


@admin_router.delete("/avatar/{avatar_id}", status_code=204)
async def delete_avatar(
    avatar_id: UUID,
    service: AvatarService = Depends(get_avatar_service),
    session: AsyncSession = Depends(get_session),
):
    return await service.delete_file_and_db(session, avatar_id=avatar_id)


@admin_router.get("/avatars", response_model=Page[AvatarSchema])
async def get_avatars(
    service: UserService = Depends(get_avatar_service),
    session: AsyncSession = Depends(get_session),
):
    avatars = await service.get_list(session=session)
    if not avatars:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="avatars not found"
        )
    return avatars
