from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.core.schemas import Base
from app.language.schemas import LanguageSchema
from app.topic.schemas import TopicSchema
from app.user.schemas import AvatarSchema, UserSchema


class WordSchema(Base):
    id: UUID
    titles: dict[str, str]
    image: str
    audio: dict[str, str]
    topic: Optional[TopicSchema] = None
    media_missing: Optional[bool] = False

class LessonSchema(Base):
    id: UUID
    lesson_id_mobile: Optional[str] = None
    is_block: bool
    topic: Optional[TopicSchema] = None
    user: Optional[UserSchema] = None
    progress_lesson_stars: int = 0
    words: List[WordSchema]
    created_at: datetime
    updated_at: datetime


class LessonWithoutUserSchema(Base):
    id: UUID
    lesson_id_mobile: Optional[str] = None
    progress_lesson_stars: int = 0
    is_block: bool
    words: List[WordSchema]


class UserLessonsSchema(Base):
    user: UserSchema
    lessons: List[LessonWithoutUserSchema]


class UpdateLessonSchema(Base):
    is_block: Optional[bool] = None
    topic_id: Optional[UUID] = None


class ResponsePaginationLessons(Base):
    items: List[LessonSchema]
    total: int
    page: int
    size: int
    pages: int


class RouletteLessonSchema(Base):
    language: LanguageSchema
    words: List[WordSchema]


class ProgressCreateSchema(Base):
    lesson_id: UUID
    language_id: UUID
    stars: int = Field(..., ge=0, le=4)


class RouletteProgressCreateSchema(Base):
    language_id: UUID
    stars: int = Field(..., ge=0, le=18)


class RouletteProgressResponseSchema(Base):
    total_stars: int


class ProgressSchema(Base):
    id: UUID
    user_id: UUID
    lesson_id: UUID
    stars: int
    created_at: datetime
    updated_at: datetime


class LeaderboardUserSchema(Base):
    id: UUID
    name: str
    avatar: Optional[AvatarSchema]
    total_stars: int
    place: int
    is_current_user: bool


class LeaderboardResponseSchema(Base):
    top_users: List[LeaderboardUserSchema]  # первые 10 + мой результат
    current_user_result: Optional[LeaderboardUserSchema]  # если вне топа
