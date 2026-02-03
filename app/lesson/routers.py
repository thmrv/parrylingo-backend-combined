import json
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database_async import get_session
from app.lesson.dependencies import get_favorite_user_lesson_service, get_lesson_service
from app.lesson.schemas import (
    LeaderboardResponseSchema,
    LessonSchema,
    ProgressCreateSchema,
    ProgressSchema,
    ResponsePaginationLessons,
    RouletteProgressCreateSchema,
    RouletteProgressResponseSchema,
    UpdateLessonSchema,
    UserLessonsSchema,
    WordSchema,
)
from app.lesson.services import LessonService
from app.user.auth.dependencies import get_current_user, get_current_user_optional
from app.user.dependencies import (
    get_user_lesson_progress_service,
    get_user_roulette_progress_service,
)
from app.user.models import User as UserModel
from app.user.services import (
    FavoriteUserLessonService,
    LeaderboardService,
    UserLessonProgressService,
    UserLessonRouletteProgressService,
)

router = APIRouter()
admin_router = APIRouter(prefix="/admin")


@router.post(
    "/lesson/base64", status_code=status.HTTP_201_CREATED, response_model=LessonSchema
)
async def create_lesson_base64(
    creator_name: Optional[str] = Form("John Dow"),
    lesson_id: Optional[str] = Form(None),
    language_code: str = Form(...),
    topic: Optional[str] = Form(None),
    word1_titles: str = Form(...),
    word1_image_base64: str = Form(...),
    word1_audio_base64: str = Form(...),
    word2_titles: str = Form(...),
    word2_image_base64: str = Form(...),
    word2_audio_base64: str = Form(...),
    lesson_service: LessonService = Depends(get_lesson_service),
    session: AsyncSession = Depends(get_session),
):
    debug_payload = {
        "creator_name": creator_name,
        "lesson_id": lesson_id,
        "language_code": language_code,
        "topic": topic,
        "word1_titles": word1_titles,
        "word1_image_base64": word1_image_base64[:100],
        "word1_audio_base64": word1_audio_base64[:100],
        "word2_titles": word2_titles,
        "word2_image_base64": word2_image_base64[:100],
        "word2_audio_base64": word2_audio_base64,
    }

    debug_path = Path("/tmp/lesson_base64_debug.json")
    debug_path.write_text(json.dumps(debug_payload, indent=2, ensure_ascii=False))

    raw_words = [
        {
            "titles": word1_titles,
            "image_base64": word1_image_base64,
            "audio_base64": word1_audio_base64,
        },
        {
            "titles": word2_titles,
            "image_base64": word2_image_base64,
            "audio_base64": word2_audio_base64,
        },
    ]
    return await lesson_service.create_lesson_from_base64(
        session,
        name=creator_name,
        raw_words=raw_words,
        lesson_id_mobile=lesson_id,
        topic=topic,
    )


@router.get(
    "/lessons",
    response_model=ResponsePaginationLessons,
    summary="Список уроков (с прогрессом, если авторизован)",
)
async def get_list_lessons(
    lesson_service: LessonService = Depends(get_lesson_service),
    session: AsyncSession = Depends(get_session),
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    language_id: Optional[UUID] = Query(None, description="Language id"),
    topic_id: Optional[UUID] = Query(None, description="Topic id"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Поиск по titles слов"),
):
    return await lesson_service.get_list_new(
        session=session,
        page=page,
        size=size,
        search=search,
        user_id=(current_user.id if current_user else None),
        language_id=language_id,
        topic_id=topic_id,
        is_block=False,
    )


@admin_router.get("/lessons", response_model=ResponsePaginationLessons)
async def get_full_list_lessons(
    lesson_service: LessonService = Depends(get_lesson_service),
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
):
    return await lesson_service.get_list_new(
        session,
        page=page,
        size=size,
    )


@admin_router.patch("/lesson/{lesson_id}", response_model=LessonSchema)
async def update_lesson(
    lesson_id: UUID,
    data: UpdateLessonSchema,
    lesson_service: LessonService = Depends(get_lesson_service),
    session: AsyncSession = Depends(get_session),
):
    return await lesson_service.update(session, data=data, id=lesson_id)


@router.get("/lesson/{lesson_id}", response_model=LessonSchema)
async def get_lesson(
    lesson_id: str,
    lesson_service: LessonService = Depends(get_lesson_service),
    session: AsyncSession = Depends(get_session),
):
    return await lesson_service.get_single(session, id=lesson_id)


@router.get(
    "/lessons/user/{user_id}/language/{language_id}", response_model=UserLessonsSchema
)
async def get_user_lessons_by_language(
    user_id: UUID,
    language_id: UUID,
    current_user: Optional[UserModel] = Depends(get_current_user),
    lesson_service: LessonService = Depends(get_lesson_service),
    session: AsyncSession = Depends(get_session),
):
    return await lesson_service.get_by_user_and_language(
        session, user_id=user_id, current_user=current_user, language_id=language_id
    )


@router.get(
    "/lessons/roulette",
    response_model=List[WordSchema],
    summary="Рулетка: N случайных слов-ходов",
)
async def roulette_lessons(
    count: int = Query(4, ge=1, le=18, description="Число слов"),
    lesson_service: LessonService = Depends(get_lesson_service),
    session: AsyncSession = Depends(get_session),
):
    return await lesson_service.get_roulette(session, count)


@router.delete("/lesson/{lesson_id}", response_model=LessonSchema)
async def delete_lesson(
    lesson_id: UUID,
    lesson_service: LessonService = Depends(get_lesson_service),
    session: AsyncSession = Depends(get_session),
):
    return await lesson_service.delete(session, id=lesson_id)


@router.get(
    "/authors",
    response_model=ResponsePaginationLessons,
    summary="По одному (самому свежему) уроку каждого автора",
)
async def authors_list(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    sort_by: str = Query(
        "date",
        enum=["date", "name"],
        description="Сортировка: date — от нового к старому, name — по имени автора",
    ),
    search: Optional[str] = Query(None, description="Поиск по имени автора"),
    lesson_service: LessonService = Depends(get_lesson_service),
    session: AsyncSession = Depends(get_session),
):
    return await lesson_service.list_authors(
        session=session, page=page, size=size, sort_by=sort_by, search=search
    )


@router.post(
    "/favorites/lessons",
    response_model=LessonSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить урок в избранное и вернуть этот урок",
)
async def add_favorite_lesson(
    lesson_id: UUID,
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    fav_service: FavoriteUserLessonService = Depends(get_favorite_user_lesson_service),
):
    return await fav_service.add_favorite(
        session=session, user_id=current_user.id, lesson_id=lesson_id
    )


@router.delete(
    "/favorites/lessons/{lesson_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить урок из избранного текущего пользователя",
)
async def delete_favorite_lesson(
    lesson_id: UUID,
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    fav_service: FavoriteUserLessonService = Depends(get_favorite_user_lesson_service),
):
    await fav_service.remove_favorite(
        session=session, user_id=current_user.id, lesson_id=lesson_id
    )


@router.get(
    "/favorites/lessons",
    response_model=List[LessonSchema],
    summary="Список сохранённых уроков текущего пользователя",
)
async def list_favorite_lessons(
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    fav_service: FavoriteUserLessonService = Depends(get_favorite_user_lesson_service),
):
    return await fav_service.get_favorites(session=session, user_id=current_user.id)


@router.get(
    "/favorites/lessons/roulette",
    response_model=List[WordSchema],
    summary="Рулетка: N случайных слов из избранных уроков пользователя",
)
async def roulette_favorites(
    count: int = Query(4, ge=1, le=18, description="Число слов"),
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    fav_service: FavoriteUserLessonService = Depends(get_favorite_user_lesson_service),
):
    return await fav_service.get_roulette_for_user(
        session=session, user_id=current_user.id, count=count
    )


@router.post(
    "/progress/lessons",
    response_model=ProgressSchema,
    status_code=status.HTTP_200_OK,
    summary="Записать или обновить прогресс пользователя по уроку",
)
async def record_lesson_progress(
    body: ProgressCreateSchema,
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    prog_service: UserLessonProgressService = Depends(get_user_lesson_progress_service),
):
    return await prog_service.record_progress(
        session=session,
        user_id=current_user.id,
        lesson_id=body.lesson_id,
        language_id=body.language_id,
        stars=body.stars,
    )


@router.post(
    "/progress/roulette",
    response_model=RouletteProgressResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Записать прогресс пользователя за прохождение рулетки",
)
async def record_roulette_progress(
    body: RouletteProgressCreateSchema,
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    prog_roulette_service: UserLessonRouletteProgressService = Depends(
        get_user_roulette_progress_service
    ),
):
    return await prog_roulette_service.record_roulette(
        session=session,
        user_id=current_user.id,
        stars=body.stars,
        language_id=body.language_id,
    )


@router.get(
    "/leaderboard/{language_id}",
    response_model=LeaderboardResponseSchema,
    summary="Получить лидерборд по языку",
)
async def get_leaderboard(
    language_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    service = LeaderboardService(session)
    return await service.get_leaderboard(language_id, current_user.id)


@router.get(
    "/debug/user-progress/{language_id}", summary="Отладка прогресса пользователя"
)
async def debug_user_progress(
    language_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    service = LeaderboardService(session)
    return await service.debug_user_progress(language_id, current_user.id)
