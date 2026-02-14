from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.models import Base, TimestampMixin, UUIDIDMixin


class Language(Base, UUIDIDMixin, TimestampMixin):
    __tablename__ = "language"

    # название языка, например "English"
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    language_code: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)
    # связь на уроки
