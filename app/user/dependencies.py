from app.email.dependencies import get_email_service
from app.lesson.repositories import LessonRepository
from app.user.repositories import (
    AvatarRepository,
    UserLessonProgressRepository,
    UserLessonRouletteProgressRepository,
    UserRepository,
)
from app.user.services import (
    AvatarService,
    UserLessonProgressService,
    UserLessonRouletteProgressService,
    UserService,
)


def get_user_service() -> UserService:
    user_repo = UserRepository()
    lesson_repo = LessonRepository()
    email_service = get_email_service()
    return UserService(user_repo, lesson_repo, email_service)


def get_avatar_service() -> AvatarService:
    avatar_repo = AvatarRepository()
    return AvatarService(avatar_repo)


def get_user_lesson_progress_service() -> UserLessonProgressService:
    return UserLessonProgressService(UserLessonProgressRepository(), UserRepository())


def get_user_roulette_progress_service() -> UserLessonRouletteProgressService:
    return UserLessonRouletteProgressService(
        UserLessonRouletteProgressRepository(), UserRepository()
    )
