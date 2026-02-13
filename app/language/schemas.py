from uuid import UUID

from app.core.schemas import Base


class LanguageSchema(Base):
    id: UUID
    name: str
    language_code: str
    interface_flag_code: str
