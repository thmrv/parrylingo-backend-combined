from sqlalchemy import String
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship
from sqlalchemy.orm import configure_mappers
from sqlalchemy.ext.associationproxy import association_proxy

from app.core.database.models import Base, TimestampMixin, UUIDIDMixin

class Language(Base, UUIDIDMixin, TimestampMixin):
    __tablename__ = "language"

    # название языка, например "English"
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    language_code: Mapped[str] = mapped_column(String(100), ForeignKey('interface.language_code'), primary_key=True, nullable=True, unique=True)
    
    interface: Mapped["Interface"] = relationship(
        "Interface", 
        back_populates="language",
        foreign_keys="[Interface.language_code]",
        uselist=False
    )
    
    flag_code: Mapped[str] = association_proxy("interface", "flag_code")