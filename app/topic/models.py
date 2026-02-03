from typing import List

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.models import Base, TimestampMixin, UUIDIDMixin


class Topic(Base, UUIDIDMixin, TimestampMixin):
    __tablename__ = "topic"  # noqa

    names: Mapped[dict] = mapped_column(JSONB, nullable=False)

    lessons: Mapped[List["Lesson"]] = relationship(
        "Lesson",
        back_populates="topic",
        passive_deletes=True,  # чтобы SQL-сторона обрабатывала ondelete
    )
