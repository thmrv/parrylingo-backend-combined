import base64
import json
import math
import mimetypes
import traceback
import re
from io import BytesIO
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from app.core.database.database_async import get_session

from fastapi import HTTPException
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import UploadFile as StarletteUploadFile
from fastapi.testclient import TestClient

from app.core.utils import get_background_tasks
from redis.asyncio import Redis
from app.core.database.redis import get_redis 

import httpx
import asyncio
import logging

from app.core.services import BaseService
from app.core.utils import remove_media_file, save_upload_file
from app.language.repositories import LanguageRepository
from app.lesson.mappers import (
    lesson_mapper,
    lesson_without_user_mapper,
    user_mapper,
    word_mapper,
    word_mapper_roulette
)
from app.lesson.models import Lesson
from app.lesson.repositories import LessonRepository, WordRepository
from app.lesson.schemas import (
    LessonSchema,
    ResponsePaginationLessons,
    UpdateLessonSchema,
    UserLessonsSchema,
    WordSchema,
)
from app.topic.dependencies import get_topic_service
from app.user.dependencies import get_user_service
from app.user.models import User
from app.user.repositories import UserLessonProgressRepository, UserRepository
from loggers import get_logger

from app.core.settings import settings

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)

class LessonService(BaseService):

    def __init__(
        self,
        repository: LessonRepository,
        word_repo: WordRepository,
        language_repo: LanguageRepository,
        user_repo: UserRepository,
        progress_repo: UserLessonProgressRepository,
    ):
        super().__init__(repository)
        self.word_repo = word_repo
        self.language_repo = language_repo
        self.user_repo = user_repo
        self.progress_repo = progress_repo,

    async def create_lesson(
        self,
        session: AsyncSession,
        words: List[Dict],
        lesson_id_mobile: Optional[int] = None,
        user_id: Optional[UUID] = None,
        topic_id: Optional[UUID] = None,
    ) -> Optional[Lesson]:
        lesson_data = {
            "lesson_id_mobile": lesson_id_mobile,
            "user_id": user_id,
            "topic_id": topic_id,
        }
        lesson = await self.repository.create(session, data=lesson_data, commit=False)
        await session.flush()
        logger.info("Lesson %s created and flushed", lesson.id)

        for w in words:
            # Сохраняем image
            image_path = await save_upload_file(w["image"], subdir="image")

            # audio — уже dict: {"ru": "...", "en": "..."}
            audio_paths = w["audio"]  # сохраняем напрямую

            word_data = {
                "lesson_id": lesson.id,
                "titles": (
                    json.loads(w["titles"])
                    if isinstance(w["titles"], str)
                    else w["titles"]
                ),
                "image_url": image_path,
                "audio_url": audio_paths,  # сохраняем JSONB
            }
            word = await self.word_repo.create(session, word_data)
            logger.info(
                "Word %s ('%s') created for lesson %s", word.id, w["titles"], lesson.id
            )

        await session.commit()
        logger.info("Committed lesson %s and its words to the database", lesson.id)

        await session.refresh(lesson, attribute_names=["words", "user"])
        logger.info("Refreshed lesson %s with related entities", str(lesson.id))

        result = lesson_mapper(lesson)
        logger.info("Returning created lesson %s", str(lesson.id))
        
        launch_audio_validation_status = await self.requestAudioValidation(25)
        logger.info("Launched audio validation with return status: %s", launch_audio_validation_status)
        
        return result

    async def requestAudioValidation(self, offset: int):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.base_url}admin/trigger-validation?offset={offset}")
            assert response.status_code == 200

    async def create_lesson_from_base64(
        self,
        session: AsyncSession,
        raw_words: list[dict],
        lesson_id_mobile: Optional[int] = None,
        topic: Optional[str] = None,
        name: Optional[str] = None,
    ):
        def decode_base64_file(data: str) -> StarletteUploadFile:
            match = re.match(r"data:(.*?);base64,(.*)", data)
            if match:
                mime_type, base64_data = match.groups()
                ext = mimetypes.guess_extension(mime_type) or ""
            else:
                base64_data = data
                ext = ""

            file_data = base64.b64decode(base64_data)
            filename = f"{uuid4().hex}{ext}"
            return StarletteUploadFile(filename=filename, file=BytesIO(file_data))

        user = await get_user_service().get_or_create_by_name(session, name=name)
        topic_info = await get_topic_service().get_single_by_name(session, name=topic)

        words = []
        for raw in raw_words:
            image = decode_base64_file(raw["image_base64"])

            # Обработка titles
            titles_raw = (
                json.loads(raw["titles"])
                if isinstance(raw["titles"], str)
                else raw["titles"]
            )
            if isinstance(titles_raw, list):
                titles = {k: v for d in titles_raw for k, v in d.items()}
            else:
                titles = titles_raw

            # Обработка audio_base64 по языкам
            audio_raw = (
                json.loads(raw["audio_base64"])
                if isinstance(raw["audio_base64"], str)
                else raw["audio_base64"]
            )
            if isinstance(audio_raw, list):
                audio_dict = {k: v for d in audio_raw for k, v in d.items()}
            else:
                audio_dict = audio_raw

            audio_paths = {}
            for lang, base64_audio in audio_dict.items():
                decoded_audio = decode_base64_file(base64_audio)
                saved_path = await save_upload_file(
                    decoded_audio, subdir="audio", convert_to_mp3=True
                )
                audio_paths[lang] = saved_path

            words.append(
                {
                    "titles": titles,
                    "image": image,
                    "audio": audio_paths,  # dict вида {"ru": "...", "en": "..."}
                }
            )

        return await self.create_lesson(
            session=session,
            words=words,
            lesson_id_mobile=lesson_id_mobile,
            user_id=user.id,
            topic_id=topic_info.id if topic_info else None,
        )

    async def update(
        self, session: AsyncSession, data: UpdateLessonSchema, **filters
    ) -> Optional[LessonSchema]:
        """Update a record matching the filters using the provided session."""
        lesson_update = await self.repository.update(
            session, data.model_dump(exclude_unset=True), **filters
        )
        if not lesson_update:
            raise HTTPException(status_code=404, detail="Lesson not found")

        return lesson_mapper(lesson_update)

    async def get_list_new(
        self,
        session: AsyncSession,
        page: int,
        size: int,
        *,
        search: Optional[str] = None,
        user_id: Optional[UUID] = None,
        language_id: Optional[UUID] = None,
        **filters,
    ) -> ResponsePaginationLessons:
        language_code = None
        if language_id:
            language = await self.language_repo.get_single(session, id=language_id)
            if language:
                language_code = language.language_code

        lessons, total = await self.repository.get_list_without_pagination_new(
            session=session,
            page=page,
            size=size,
            search=search,
            language_code=language_code,
            **filters,
        )

        progress_map: dict[UUID, int] = {}
        if user_id:
            ids = [lesson.id for lesson in lessons]
            progresses = await self.progress_repo.list_by_user_and_lessons(
                session, user_id, language_id, ids
            )
            progress_map = {p.lesson_id: p.stars for p in progresses}

        items = []
        for lesson in lessons:
            dto = lesson_mapper(lesson)
            dto.progress_lesson_stars = progress_map.get(lesson.id, 0)
            items.append(dto)

        return ResponsePaginationLessons(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size),
        )

    async def get_by_user_and_language(
        self,
        session: AsyncSession,
        user_id: UUID,
        current_user: User,
        language_id: UUID,
    ) -> UserLessonsSchema:
        user = await self.user_repo.get_single(session, id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        lessons = await self.repository.get_list_without_pagination(
            session, user_id=user_id, is_block=False
        )

        # получаем список ID уроков
        lesson_ids = [lesson.id for lesson in lessons]

        # вытаскиваем прогресс по урокам текущего пользователя
        progresses = await self.progress_repo.list_by_user_and_lessons(
            session,
            user_id=current_user.id,
            language_id=language_id,
            lesson_ids=lesson_ids,
        )
        progress_map = {p.lesson_id: p.stars for p in progresses}

        # собираем DTO с подставленным progress_lesson_stars
        lessons_dto = []
        for lesson in lessons:
            dto = lesson_without_user_mapper(lesson)
            dto.progress_lesson_stars = progress_map.get(lesson.id, 0)
            lessons_dto.append(dto)

        return UserLessonsSchema(
            user=user_mapper(user),
            lessons=lessons_dto,
        )

    async def get_single(self, session: AsyncSession, **filters) -> LessonSchema:

        if "id" in filters:
            try:
                # Проверим, является ли это валидным UUID
                UUID(filters["id"])
                lesson = await self.repository.get_single(session, id=filters["id"])
            except ValueError:
                # если не UUID, пробуем искать по lesson_id_mobile
                lesson = await self.repository.get_single(
                    session, lesson_id_mobile=filters["id"]
                )
        else:
            lesson = await self.repository.get_single(session, **filters)

        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")

        return lesson_mapper(lesson)

    async def get_roulette(
        self, session: AsyncSession, count: int = 4
    ) -> list[WordSchema]:
        words = await self.word_repo.get_random_words_by_topic(session, count)
        return [word_mapper_roulette(w) for w in words]

    async def delete(self, session: AsyncSession, **filters) -> Optional[Lesson]:
        logger.info("Attempting to delete lesson with filters %s", filters)
        lesson = await self.repository.get_single(session, **filters)
        if not lesson:
            logger.warning("Lesson not found for filters %s", filters)
            raise HTTPException(status_code=404, detail="Lesson not found")

        # 1) собираем пути файлов
        media_paths = [p for w in lesson.words for p in (w.image_url, w.audio_url)]
        logger.info("Media files to remove for lesson %s: %s", lesson.id, media_paths)

        # 2) удаляем записи из БД
        await self.repository.delete(session, **filters)
        logger.info("Lesson %s deleted from database", lesson.id)

        # 3) удаляем файлы
        for rel_path in media_paths:
            await remove_media_file(rel_path)
            logger.info("Removed media file %s for lesson %s", rel_path, lesson.id)

        result = lesson_mapper(lesson)
        logger.info("Returning deleted lesson %s", lesson.id)
        return result

    async def list_authors(
        self,
        session: AsyncSession,
        page: int = 1,
        size: int = 10,
        sort_by: str = "date",
        search: Optional[str] = None,
    ) -> ResponsePaginationLessons:
        lessons, total = await self.repository.get_latest_lessons_per_author(
            session=session, search=search, page=page, size=size
        )

        # 1 урок на автора уже отобран — теперь сортируем
        if sort_by == "name":
            lessons.sort(key=lambda lesson: (lesson.user.name or "").lower())
        else:  # по дате: от новейшего к старому
            lessons.sort(key=lambda lesson: lesson.created_at, reverse=True)

        items = [
            lesson_mapper(lesson) for lesson in lessons
        ]  # маппер возвращает LessonSchema

        return ResponsePaginationLessons(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size),
        )
        
class AudioValidationService:
    BASE_URL = settings.media_base_url

    def __init__(self, repository: WordRepository, session: AsyncSession, redis: Redis = Depends(get_redis), offset: int = 0):
        self.redis = redis
        self.repository = repository
        self.session = session
        self.offset = offset

    async def run_background_validation(self):
        words = await self.repository.get_all_with_audio(self.session, self.offset)
        failed_word_ids = set()
        
        try:
            lock_acquired = await self.redis.set("audio_validation_lock", "running", ex=3600, nx=True)
                
            tasks = []
            async with httpx.AsyncClient(timeout=10.0) as client:
                semaphore = asyncio.Semaphore(10)

                print("BACKGROUND TASK:    AUDIO VALIDATION TASK STARTED")
                        
                for word in words:
                    for locale, path in word.audio_url.items():
                        if isinstance(path, str) and path.startswith('audio'):
                            word_id, is_failed = await self._check_url(client, path, word.id, semaphore)
                            if is_failed:
                                logger.warning(f"Word {word_id} failed on {locale}. Skipping other locales.")
                                failed_word_ids.add(word_id)
                                break 

            if failed_word_ids:
                await self.repository.mark_words_as_missing(list(failed_word_ids))
                print("BACKGROUND TASK:    AUDIO VALIDATION TASK FINISHED")
                logger.info(f"Validation complete. Marked {len(failed_word_ids)} words out of {len(words)} as media_missing=True")
                await self.redis.delete("audio_validation_lock")
            else:
                print("BACKGROUND TASK:    AUDIO VALIDATION TASK FINISHED: ALL FOUND")
                logger.info(f"Validation complete. All media found [{len(words)}] words")
                await self.redis.delete("audio_validation_lock")
        except Exception as e:
            verbose_error = traceback.format_exc()
            print("BACKGROUND TASK:    AUDIO VALIDATION TASK FAILED: \n" + verbose_error)
            logger.error("Validation failed: \n" + verbose_error)
            await self.redis.delete("audio_validation_lock")
            return

    async def _check_url(self, client, path, word_id, semaphore):
        async with semaphore:
            url = f"{self.BASE_URL}{path}"
            try:
                response = await client.head(url)
                # If 404
                logger.info("URL checked: %s", response.status_code)
                return word_id, response.status_code != 200
            except Exception as e:
                verbose_error = traceback.format_exc()
                print("BACKGROUND TASK:    URL CHECKED: EXCEPTION: " + verbose_error)
                return word_id, True
