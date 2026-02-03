from datetime import datetime
from typing import Optional
from uuid import UUID

from app.core.schemas import Base


class CreateUserModel(Base):
    avatar_id: Optional[UUID] = None
    email: str
    name: str
    password: str


class AvatarSchema(Base):
    id: UUID
    link: str


class UserProfileViewModel(Base):
    id: UUID
    name: str
    email: Optional[str] = None
    avatar: Optional[AvatarSchema] = None
    total_stars: Optional[int] = None
    is_block: Optional[bool] = None
    created_at: datetime
    updated_at: datetime


class UserBlockShema(Base):
    is_block: bool


class ProfileUpdate(Base):
    name: Optional[str] = None
    avatar_id: Optional[UUID] = None


class LoginUserModel(Base):
    email: str
    password: str


class WelcomeTemplate(Base):
    name: str
    email: str
    password: str


class UserSchema(Base):
    id: UUID
    name: str
    avatar: Optional[AvatarSchema] = None
