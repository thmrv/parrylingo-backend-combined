from app.language.repositories import LanguageRepository
from app.lesson.repositories import LessonRepository, WordRepository
from app.lesson.services import LessonService
from app.user.repositories import (
    FavoriteUserLessonRepository,
    UserLessonProgressRepository,
    UserRepository,
)
from app.user.services import FavoriteUserLessonService


def get_lesson_service() -> LessonService:
    lesson_repo = LessonRepository()
    word_repo = WordRepository()
    language_repo = LanguageRepository()
    user_repo = UserRepository()
    progress_repo = UserLessonProgressRepository()
    return LessonService(
        lesson_repo, word_repo, language_repo, user_repo, progress_repo
    )


def get_favorite_user_lesson_service() -> FavoriteUserLessonService:
    favorite_user_repo = FavoriteUserLessonRepository()
    lesson_repo = LessonRepository()
    word_repo = WordRepository()
    return FavoriteUserLessonService(favorite_user_repo, lesson_repo, word_repo)
