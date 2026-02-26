from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship
from sqlalchemy.orm import configure_mappers

from app.core.database.models import Base, TimestampMixin

class Interface(Base, TimestampMixin):
    __tablename__ = "interface"

    name: Mapped[str] = mapped_column(String, nullable=False)
    language_code: Mapped[str] = mapped_column(String, ForeignKey("language.language_code"), primary_key=True, nullable=False, unique=True)   
    flag_code: Mapped[str] = mapped_column(String, nullable=False)
    interface: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    language: Mapped["Language"] = relationship(
        "Language", 
        foreign_keys=[language_code],
        back_populates="interface",
        cascade="all, delete-orphan",
        single_parent=True 
    )