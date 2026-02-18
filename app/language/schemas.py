from uuid import UUID
from pydantic import BaseModel, ConfigDict, model_validator
from typing import Optional
from sqlalchemy import inspect

from app.core.schemas import Base

from app.interface.schemas import InterfaceSchema

class LanguageSchema(Base):
    id: UUID
    name: str
    language_code: str
    #interface: Optional[InterfaceSchema] = None
    
    flag_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
