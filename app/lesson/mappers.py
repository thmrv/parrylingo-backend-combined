from app.lesson.models import Lesson, Word
from app.lesson.schemas import LessonSchema, LessonWithoutUserSchema, WordSchema
from app.user.models import User
from app.user.schemas import UserSchema


def user_mapper(user: User) -> UserSchema:
    return UserSchema(
        id=user.id,
        name=user.name,
    )


def word_mapper(word: Word) -> WordSchema:
    return WordSchema(
        id=word.id,
        titles=word.titles,
        image=word.image_url,
        audio=word.audio_url,
    )


def lesson_mapper(lesson: Lesson) -> LessonSchema:
    return LessonSchema(
        id=lesson.id,
        lesson_id_mobile=lesson.lesson_id_mobile,
        is_block=lesson.is_block,
        topic=lesson.topic,
        user=user_mapper(lesson.user) if lesson.user else None,
        words=[word_mapper(w) for w in lesson.words],
        created_at=lesson.created_at,
        updated_at=lesson.updated_at,
    )


def lesson_without_user_mapper(lesson: Lesson) -> LessonWithoutUserSchema:
    return LessonWithoutUserSchema(
        id=lesson.id,
        lesson_id_mobile=lesson.lesson_id_mobile,
        is_block=lesson.is_block,
        words=[word_mapper(w) for w in lesson.words],
    )
