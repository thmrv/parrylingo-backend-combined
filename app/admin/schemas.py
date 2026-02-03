from uuid import UUID

from app.core.schemas import Base


class LoginSuperUserSchema(Base):
    login: str
    password: str


class SuperUserProfileViewModel(Base):
    id: UUID
    login: str
