"""
This module centralizes the imports for all models to ensure that
relationships between them are properly registered and work seamlessly.
It serves as an entry point for the application's ORM to recognize and manage
table relationships effectively.
"""

from app.admin.models import SuperUser  # Noqa
from app.core.database.models import Base
from app.interface.models import Interface  # noqa
from app.language.models import Language  # noqa
from app.lesson.models import Lesson, Word  # noqa
from app.topic.models import Topic  # noqa
from app.user.models import Avatar, FavoriteUserLesson, User  # noqa

__all__ = ["Base"]
