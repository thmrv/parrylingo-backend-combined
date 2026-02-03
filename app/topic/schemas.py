from typing import Dict
from uuid import UUID

from app.core.schemas import Base


class TopicBase(Base):
    names: Dict[str, str]


class TopicCreate(TopicBase):
    pass


class TopicUpdate(Base):
    names: Dict[str, str] | None = None


class TopicSchema(TopicBase):
    id: UUID

    class Config:
        orm_mode = True
