from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.models import Base, TimestampMixin


class Interface(Base, TimestampMixin):
    __tablename__ = "interface"

    name: Mapped[str] = mapped_column(String, nullable=False)
    language_code: Mapped[str] = mapped_column(
        String, primary_key=True, nullable=False, unique=True
    )
    flag_code: Mapped[str] = mapped_column(String, nullable=False)
    interface: Mapped[dict] = mapped_column(JSONB, nullable=False)
