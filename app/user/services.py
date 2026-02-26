from typing import List, Optional, Union
from uuid import UUID

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import UploadFile

from app.core.services import BaseService
from app.core.utils import remove_media_file, save_upload_file, verify_password
from app.email.service import EmailService
from app.lesson.mappers import lesson_mapper, word_mapper
from app.lesson.repositories import LessonRepository, WordRepository
from app.lesson.schemas import (
    LeaderboardResponseSchema,
    LeaderboardUserSchema,
    LessonSchema,
    ProgressSchema,
    RouletteProgressResponseSchema,
    WordSchema,
)
from app.user.auth.schemas import TokenModel
from app.user.auth.security import create_access_token, create_refresh_token
from app.user.models import (
    Avatar,
    FavoriteUserLesson,
    User,
    UserLessonProgress,
    UserLessonRouletteProgress,
)
from app.user.repositories import (
    AvatarRepository,
    FavoriteUserLessonRepository,
    UserLessonProgressRepository,
    UserLessonRouletteProgressRepository,
    UserRepository,
)
from app.user.schemas import (
    AvatarSchema,
    CreateUserModel,
    LoginUserModel,
    WelcomeTemplate,
)


class UserService(BaseService):

    def __init__(
        self,
        repository: UserRepository,
        lesson_repo: LessonRepository,
        email_service: EmailService,
    ):
        super().__init__(repository)
        self.lesson_repo = lesson_repo
        self.email_service = email_service

    async def create_user_and_send_info_to_email(
        self,
        session: AsyncSession,
        data: CreateUserModel,
        background_tasks: BackgroundTasks,
    ):

        user = await self.create(session=session, data=data)
        if user:
            body = WelcomeTemplate(
                name=user.name, email=user.email, password=data.password
            )
            background_tasks.add_task(self.send_info_to_email, template_body=body)

        return user

    async def send_info_to_email(self, template_body: WelcomeTemplate):
        await self.email_service.send_template_email(
            subject="Добро пожаловать!",
            recipients=template_body.email,
            template_name="welcome.html",
            template_body=template_body,
        )

    async def authenticate_user(
        self, session: AsyncSession, data: LoginUserModel
    ) -> Union[TokenModel, bool]:
        user = await self.repository.get_single(session, email=data.email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not verify_password(data.password, user.password):
            raise HTTPException(status_code=400, detail="Password incorrect")

        token_data = {"sub": str(user.id)}

        return TokenModel(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
        )

    async def get_or_create_by_name(self, session: AsyncSession, name: str) -> User:
        user = await self.repository.get_single(session, name=name)
        if user:
            return user
        return await self.repository.create(session, data={"name": name})


class AvatarService(BaseService):

    def __init__(self, repository: AvatarRepository):
        super().__init__(repository)

    async def create(
        self, session: AsyncSession, avatar: UploadFile
    ) -> Optional[Avatar]:
        avatar_path = await save_upload_file(avatar, subdir="avatars")
        return await self.repository.create(session, data={"link": avatar_path})

    async def delete_file_and_db(self, session: AsyncSession, avatar_id: UUID):
        avatar = await self.repository.get_single(session, id=avatar_id)
        await remove_media_file(avatar.link)
        await self.repository.delete(session, id=avatar_id)


class FavoriteUserLessonService(BaseService):
    def __init__(
        self,
        repository: FavoriteUserLessonRepository,
        lesson_repo: LessonRepository,
        word_repo: WordRepository,
    ):
        super().__init__(repository)
        self.lesson_repo = lesson_repo
        self.word_repo = word_repo

    async def add_favorite(
        self, session: AsyncSession, user_id: UUID, lesson_id: UUID
    ) -> LessonSchema:
        # 1) проверяем, не было ли уже
        exists = await self.repository.get_single(
            session, user_id=user_id, lesson_id=lesson_id
        )
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lesson is already in favorites",
            )

        # 2) создаём запись в favorite_user_lesson
        await self.repository.create(
            session, data={"user_id": user_id, "lesson_id": lesson_id}
        )

        # 3) подгружаем сам Lesson вместе со словами, языком и пользователем
        lesson = await self.lesson_repo.get_single(
            session,
            id=lesson_id,
        )
        if not lesson:
            # маловероятно, но на всякий случай
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found"
            )

        # 4) возвращаем в виде вашего LessonSchema
        return lesson_mapper(lesson)

    async def remove_favorite(
        self, session: AsyncSession, user_id: UUID, lesson_id: UUID
    ) -> None:
        # 1) находим запись
        fav: FavoriteUserLesson | None = await self.repository.get_single(
            session, user_id=user_id, lesson_id=lesson_id
        )
        if not fav:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Favorite entry not found"
            )
        # 2) удаляем и коммитим
        await self.repository.delete(session, lesson_id=lesson_id)

    async def get_favorites(
        self, session: AsyncSession, user_id: UUID
    ) -> List[LessonSchema]:
        lessons = await self.repository.list_user_favorite_lessons(session, user_id)
        return [lesson_mapper(lesson) for lesson in lessons]

    async def get_roulette_for_user(
        self, session: AsyncSession, user_id: UUID, count: int = 4, topic_id: str = None
    ) -> List[WordSchema]:
        words = await self.word_repo.get_random_words_for_user(session, user_id, count, topic_id)
        return [word_mapper(word) for word in words]


class UserLessonProgressService(BaseService):
    def __init__(
        self, repository: UserLessonProgressRepository, user_repo: UserRepository
    ):
        super().__init__(repository)
        self.user_repo = user_repo

    async def record_progress(
        self,
        session: AsyncSession,
        user_id: UUID,
        lesson_id: UUID,
        language_id: UUID,
        stars: int,
    ) -> ProgressSchema:
        # 1) найдём существующую запись
        existing = await self.repository.get_single(
            session, user_id=user_id, lesson_id=lesson_id, language_id=language_id
        )

        # 2) вычислим дельту
        if existing:
            if stars <= existing.stars:
                # ничего не делаем
                return ProgressSchema.from_orm(existing)
            delta = stars - existing.stars
            existing.stars = stars
            await session.commit()
            await session.refresh(existing)
            prog = existing
        else:
            delta = stars
            prog = await self.repository.create(
                session,
                data={
                    "user_id": user_id,
                    "lesson_id": lesson_id,
                    "language_id": language_id,
                    "stars": stars,
                },
            )

        # 3) обновим total_stars юзера
        user = await self.user_repo.get_single(session, id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.total_stars = (user.total_stars or 0) + delta
        await session.commit()
        # не обязательно refresh юзера

        return ProgressSchema.from_orm(prog)


class UserLessonRouletteProgressService(BaseService):
    def __init__(
        self, repo: UserLessonRouletteProgressRepository, user_repo: UserRepository
    ):
        super().__init__(repo)
        self.user_repo = user_repo

    async def record_roulette(
        self, session: AsyncSession, user_id: UUID, stars: int, language_id: UUID
    ) -> RouletteProgressResponseSchema:
        user = await self.user_repo.get_single(session, id=user_id)
        await self.repository.create(
            session,
            data={"user_id": user_id, "language_id": language_id, "stars": stars},
        )
        user.total_stars = (user.total_stars or 0) + stars
        await session.commit()
        return RouletteProgressResponseSchema(total_stars=user.total_stars)


class LeaderboardService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_leaderboard(
        self, language_id: UUID, current_user_id: UUID
    ) -> LeaderboardResponseSchema:
        print(
            f"Getting leaderboard for language_id: {language_id}, current_user_id: {current_user_id}"
        )

        # Сначала проверим, есть ли данные в принципе
        test_query = await self.session.execute(
            select(func.count())
            .select_from(UserLessonProgress)
            .where(UserLessonProgress.language_id == language_id)
        )
        lesson_count = test_query.scalar()
        print(f"Records in UserLessonProgress for language: {lesson_count}")

        test_query2 = await self.session.execute(
            select(func.count())
            .select_from(UserLessonRouletteProgress)
            .where(UserLessonRouletteProgress.language_id == language_id)
        )
        roulette_count = test_query2.scalar()
        print(f"Records in UserLessonRouletteProgress for language: {roulette_count}")

        # Давайте проверим пользователя отдельно
        print("Checking user exists and not blocked...")
        user_check = await self.session.execute(
            select(User.id, User.name, User.is_block).where(User.id == current_user_id)
        )
        user_data = user_check.fetchone()
        print(f"User data: {user_data}")

        # Проверим UNION отдельно
        print("Testing UNION query...")
        union_query = (
            select(UserLessonProgress.user_id)
            .where(UserLessonProgress.language_id == language_id)
            .union(
                select(UserLessonRouletteProgress.user_id).where(
                    UserLessonRouletteProgress.language_id == language_id
                )
            )
        )
        union_result = await self.session.execute(union_query)
        union_users = union_result.fetchall()
        print(f"Union results: {[str(r.user_id) for r in union_users]}")

        # Давайте попробуем более простой подход без CTE
        # Сначала тестируем простой запрос только по урокам
        print("Testing lesson stars query...")
        lesson_test = await self.session.execute(
            select(
                UserLessonProgress.user_id,
                func.sum(UserLessonProgress.stars).label("lesson_stars"),
            )
            .where(UserLessonProgress.language_id == language_id)
            .group_by(UserLessonProgress.user_id)
        )
        lesson_results = lesson_test.fetchall()
        print(
            f"Lesson stars results: {[(str(r.user_id), r.lesson_stars) for r in lesson_results]}"
        )

        # Тестируем простой JOIN с исправленным условием
        print("Testing simple JOIN...")
        simple_join = await self.session.execute(
            select(User.id, User.name, User.is_block).where(
                and_(
                    User.id.in_([current_user_id]),
                    or_(~User.is_block, User.is_block.is_(None)),
                )
            )
        )
        join_result = simple_join.fetchall()
        print(
            f"Simple JOIN result: {[(str(r.id), r.name, r.is_block) for r in join_result]}"
        )

        # Упрощенный запрос - берем всех пользователей из уроков и джойним к User
        ranked_stmt = (
            select(
                User.id.label("user_id"),
                User.name,
                User.avatar_id,
                func.coalesce(
                    select(func.sum(UserLessonProgress.stars))
                    .where(
                        and_(
                            UserLessonProgress.user_id == User.id,
                            UserLessonProgress.language_id == language_id,
                        )
                    )
                    .scalar_subquery(),
                    0,
                ).label("lesson_stars"),
                func.coalesce(
                    select(func.sum(UserLessonRouletteProgress.stars))
                    .where(
                        and_(
                            UserLessonRouletteProgress.user_id == User.id,
                            UserLessonRouletteProgress.language_id == language_id,
                        )
                    )
                    .scalar_subquery(),
                    0,
                ).label("roulette_stars"),
            )
            .where(or_(~User.is_block, User.is_block.is_(None)))
            .where(
                User.id.in_(
                    select(UserLessonProgress.user_id).where(
                        UserLessonProgress.language_id == language_id
                    )
                )
            )
        )

        print("Executing main query...")
        temp_result = await self.session.execute(ranked_stmt)
        temp_rows = temp_result.fetchall()
        print(
            f"Temp results before ranking: {[(str(r.user_id), r.lesson_stars, r.roulette_stars) for r in temp_rows]}"
        )

        # Теперь добавляем ранжирование и общие звезды
        temp_table = ranked_stmt.subquery("temp_table")
        final_stmt = (
            select(
                temp_table.c.user_id,
                temp_table.c.name,
                temp_table.c.avatar_id,
                (temp_table.c.lesson_stars + temp_table.c.roulette_stars).label(
                    "total_stars"
                ),
                func.row_number()
                .over(
                    order_by=desc(
                        temp_table.c.lesson_stars + temp_table.c.roulette_stars
                    )
                )
                .label("place"),
            )
            .where((temp_table.c.lesson_stars + temp_table.c.roulette_stars) > 0)
            .order_by(desc(temp_table.c.lesson_stars + temp_table.c.roulette_stars))
        )

        ranked_stmt = final_stmt

        # Выполняем запрос
        result = await self.session.execute(ranked_stmt)
        all_rows = result.fetchall()

        print(f"Found {len(all_rows)} users with progress")
        for row in all_rows[:5]:  # Логируем первые 5 для отладки
            print(f"User {row.name}: {row.total_stars} stars, place {row.place}")

        # 6. Загружаем аватары
        avatar_ids = list({row.avatar_id for row in all_rows if row.avatar_id})
        avatars = {}
        if avatar_ids:
            avatar_result = await self.session.execute(
                select(Avatar).where(Avatar.id.in_(avatar_ids))
            )
            avatars = {a.id: a for a in avatar_result.scalars().all()}

        # 7. Сборка топа и поиск текущего пользователя
        leaderboard_users = []
        current_user_entry = None

        for row in all_rows:
            user = LeaderboardUserSchema(
                id=row.user_id,
                name=row.name,
                avatar=(
                    AvatarSchema.from_orm(avatars[row.avatar_id])
                    if row.avatar_id in avatars
                    else None
                ),
                total_stars=row.total_stars,
                place=row.place,
                is_current_user=row.user_id == current_user_id,
            )

            # Добавляем в топ-10
            if row.place <= 10:
                leaderboard_users.append(user)

            # Запоминаем текущего пользователя
            if row.user_id == current_user_id:
                current_user_entry = user
                print(
                    f"Found current user: place {user.place}, stars {user.total_stars}"
                )

        # 8. Добавление разделителя и текущего пользователя, если он вне топа
        if current_user_entry and current_user_entry.place > 10:
            # Добавляем разделитель
            separator = LeaderboardUserSchema(
                id=UUID("00000000-0000-0000-0000-000000000000"),
                name="...",
                avatar=None,
                total_stars=0,
                place=-1,
                is_current_user=False,
            )
            leaderboard_users.append(separator)
            leaderboard_users.append(current_user_entry)

        print(f"Returning {len(leaderboard_users)} users in leaderboard")
        print(
            f"Current user result: {current_user_entry.place if current_user_entry else 'None'}"
        )

        return LeaderboardResponseSchema(
            top_users=leaderboard_users,
            current_user_result=current_user_entry,
        )

    async def debug_user_progress(self, language_id: UUID, user_id: UUID):
        """Вспомогательный метод для отладки прогресса пользователя"""

        # Проверяем прогресс в уроках
        lessons_result = await self.session.execute(
            select(
                UserLessonProgress.user_id,
                UserLessonProgress.stars,
                UserLessonProgress.language_id,
            ).where(
                and_(
                    UserLessonProgress.user_id == user_id,
                    UserLessonProgress.language_id == language_id,
                )
            )
        )
        lessons_progress = lessons_result.fetchall()

        # Проверяем прогресс в рулетке
        roulette_result = await self.session.execute(
            select(
                UserLessonRouletteProgress.user_id,
                UserLessonRouletteProgress.stars,
                UserLessonRouletteProgress.language_id,
            ).where(
                and_(
                    UserLessonRouletteProgress.user_id == user_id,
                    UserLessonRouletteProgress.language_id == language_id,
                )
            )
        )
        roulette_progress = roulette_result.fetchall()

        print(f"Debug for user {user_id}, language {language_id}:")
        print(f"Lessons progress: {len(lessons_progress)} records")
        print(f"Roulette progress: {len(roulette_progress)} records")

        total_lesson_stars = sum(row.stars for row in lessons_progress)
        total_roulette_stars = sum(row.stars for row in roulette_progress)

        print(f"Total lesson stars: {total_lesson_stars}")
        print(f"Total roulette stars: {total_roulette_stars}")
        print(f"Grand total: {total_lesson_stars + total_roulette_stars}")

        # Возвращаем простой dict вместо сложных объектов
        return {
            "lessons_count": len(lessons_progress),
            "roulette_count": len(roulette_progress),
            "total_lesson_stars": total_lesson_stars,
            "total_roulette_stars": total_roulette_stars,
            "total_stars": total_lesson_stars + total_roulette_stars,
            "lessons_details": [
                {
                    "user_id": str(row.user_id),
                    "stars": row.stars,
                    "language_id": str(row.language_id),
                }
                for row in lessons_progress
            ],
            "roulette_details": [
                {
                    "user_id": str(row.user_id),
                    "stars": row.stars,
                    "language_id": str(row.language_id),
                }
                for row in roulette_progress
            ],
        }
