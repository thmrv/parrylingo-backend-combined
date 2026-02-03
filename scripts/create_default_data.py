import asyncio
import uuid

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database_async import get_session
from app.language.models import Language
from app.lesson.models import Lesson, Word
from app.user.models import User  # Noqa


async def create_languages(session: AsyncSession) -> dict[str, uuid.UUID]:
    """Создаёт записи в таблице language и возвращает {language_code: id}."""
    languages = [("English", "en"), ("Русский", "ru")]
    langs: dict[str, uuid.UUID] = {}

    for name, code in languages:
        q = (
            insert(Language)
            .values(name=name, language_code=code)
            .returning(Language.id)
        )
        result = await session.execute(q)
        langs[code] = result.scalar_one()

    return langs


async def create_lesson_with_words(
    session: AsyncSession, language_id: uuid.UUID, num_words: int = 2
) -> uuid.UUID:
    """Создаёт один урок и заданное количество тестовых слов."""
    # 1. вставляем Lesson
    lesson_q = (
        insert(Lesson)
        .values(language_id=language_id, user_id=None)
        .returning(Lesson.id)
    )
    lesson_id = (await session.execute(lesson_q)).scalar_one()

    # 2. готовим пакет тестовых слов и вставляем их пачкой
    words = [
        {
            "lesson_id": lesson_id,
            "titles": {"en": f"Word {i}", "ru": f"Слово {i}"},
            "image_url": f"https://example.com/{language_id}/img_{i}.png",
            "audio_url": f"https://example.com/{language_id}/audio_{i}.mp3",
        }
        for i in range(1, num_words + 1)
    ]
    await session.execute(insert(Word), words)

    return lesson_id


async def seed_lessons():
    # используем ваш генератор сессий
    async for session in get_session():
        # 1) создаём языки и получаем их id
        langs = await create_languages(session)

        # 2) для каждого языка создаём по 3 урока с 2 словами
        for lang_code, cnt in (("en", 3), ("ru", 3)):
            for _ in range(cnt):
                await create_lesson_with_words(
                    session, language_id=langs[lang_code], num_words=2
                )

        # 3) коммит и выход из цикла
        await session.commit()
        print("✅ Seeded 6 lessons (3 EN + 3 FR) по 5 слов в каждом")
        break


if __name__ == "__main__":
    asyncio.run(seed_lessons())
