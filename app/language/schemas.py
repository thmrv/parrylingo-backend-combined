from uuid import UUID
from typing import Optional

from app.core.schemas import Base

from app.interface.schemas import InterfaceSchema

class LanguageSchema(Base):
    id: UUID
    name: str
    language_code: str
    flag_code: Optional[str] = None
    #interface: Optional[InterfaceSchema] = None
