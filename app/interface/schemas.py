from typing import Optional

from app.core.schemas import Base


class InterfaceCreate(Base):
    name: str
    language_code: str
    flag_code: str
    interface: dict[str, str]


class InterfaceUpdate(Base):
    language_code: Optional[str] = None
    name: Optional[str] = None
    flag_code: Optional[str] = None
    interface: Optional[dict[str, str]] = None


class InterfaceSchema(Base):
    name: str
    language_code: str
    flag_code: str
    interface: dict[str, str]
