import uuid
from typing import List

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.models import (
    Base,
    TimestampMixin,
    UUIDIDMixin,
)


class Lesson(Base, UUIDIDMixin, TimestampMixin):
    __tablename__ = "lesson"

    # поля-колонки
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=True,
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topic.id", ondelete="SET NULL"),
        nullable=True,
    )
    lesson_id_mobile: Mapped[str] = mapped_column(String, nullable=True)
    is_block: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # связи ORM
    user: Mapped["User"] = relationship("User", back_populates="lessons", lazy="joined")
    topic: Mapped["Topic"] = relationship(
        "Topic", back_populates="lessons", lazy="joined"
    )

    words: Mapped[List["Word"]] = relationship(
        "Word",
        back_populates="lesson",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="joined",
    )

    favorited_by: Mapped[List["FavoriteUserLesson"]] = relationship(
        "FavoriteUserLesson",
        back_populates="lesson",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="joined",
    )

    progress: Mapped[List["UserLessonProgress"]] = relationship(
        "UserLessonProgress",
        back_populates="lesson",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="joined",
    )


class Word(Base, UUIDIDMixin, TimestampMixin):
    __tablename__ = "word"

    # внешний ключ на урок
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lesson.id", ondelete="CASCADE"),
        nullable=False,
    )

    # собственно данные слова
    titles: Mapped[dict] = mapped_column(JSONB, nullable=False)
    image_url: Mapped[str] = mapped_column(String, nullable=False)
    audio_url: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # связь с уроком
    lesson: Mapped["Lesson"] = relationship(
        "Lesson", back_populates="words", lazy="joined"
    )
