from app.core.schemas import Base


class TokenModel(Base):
    access_token: str
    refresh_token: str


class TokenRefreshModel(Base):
    access_token: str
