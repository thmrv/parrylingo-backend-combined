from typing import List
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.database.models import Base, TimestampMixin, UUIDIDMixin
from app.core.utils import hash_password


class Avatar(Base, UUIDIDMixin, TimestampMixin):
    __tablename__ = "avatar"

    link: Mapped[str] = mapped_column(String(255), nullable=False)


class User(Base, UUIDIDMixin, TimestampMixin):
    __tablename__ = "user"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=True)
    password: Mapped[str] = mapped_column(String(150), nullable=True)
    avatar_id: Mapped[UUID] = mapped_column(
        ForeignKey("avatar.id", ondelete="SET NULL"),
        nullable=True,
    )
    total_stars: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    is_block: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)

    avatar: Mapped[Avatar] = relationship(
        "Avatar",
        uselist=False,
        lazy="joined",
    )

    lessons: Mapped[List["Lesson"]] = relationship(
        "Lesson",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="joined",
    )

    favorite_lessons: Mapped[List["FavoriteUserLesson"]] = relationship(
        "FavoriteUserLesson",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="joined",
    )

    lesson_progress: Mapped[List["UserLessonProgress"]] = relationship(
        "UserLessonProgress",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="joined",
    )

    @validates("password")
    def validate_password(self, _: str, value: str) -> str:
        if value != self.password:
            value = hash_password(value)
        return value


class FavoriteUserLesson(Base, UUIDIDMixin, TimestampMixin):
    __tablename__ = "favorite_user_lesson"
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    lesson_id: Mapped[UUID] = mapped_column(
        ForeignKey("lesson.id", ondelete="CASCADE"),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="favorite_lessons", lazy="joined"
    )

    # связь на Lesson
    lesson: Mapped["Lesson"] = relationship(
        "Lesson", back_populates="favorited_by", lazy="joined"
    )


class UserLessonProgress(Base, UUIDIDMixin, TimestampMixin):
    __tablename__ = "user_lesson_progress"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    lesson_id: Mapped[UUID] = mapped_column(
        ForeignKey("lesson.id", ondelete="CASCADE"),
        nullable=False,
    )
    language_id: Mapped[UUID] = mapped_column(
        ForeignKey("language.id", ondelete="CASCADE"),
        nullable=True,
    )

    stars: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped["User"] = relationship(
        "User",
        back_populates="lesson_progress",
        lazy="joined",
    )
    lesson: Mapped["Lesson"] = relationship(
        "Lesson",
        back_populates="progress",  # <--- это имя в Lesson
        lazy="joined",
    )


class UserLessonRouletteProgress(Base, UUIDIDMixin, TimestampMixin):
    __tablename__ = "user_lesson_roulette_progress"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    language_id: Mapped[UUID] = mapped_column(
        ForeignKey("language.id", ondelete="CASCADE"),
        nullable=True,
    )
    stars: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped["User"] = relationship(
        "User",
        lazy="joined",
    )

    language: Mapped["Language"] = relationship(
        "Language",
        backref="user_lesson_roulette_progress",
        lazy="joined",
    )
