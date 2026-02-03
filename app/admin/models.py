from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.core.database.models import Base, UUIDIDMixin
from app.core.utils import hash_password


class SuperUser(UUIDIDMixin, Base):
    __tablename__ = "super_user"  # noqa

    login: Mapped[str] = mapped_column(String(150), nullable=False)
    password: Mapped[str] = mapped_column(String(150), nullable=True)

    @validates("password")
    def validate_password(self, _: str, value: str) -> str:
        if value != self.password:
            value = hash_password(value)
        return value

    def __repr__(self):
        return f"<SuperUser(id={str(self.id)}, login={self.login!r}"
