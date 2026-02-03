from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database_async import get_session
from app.language.dependencies import get_language_service
from app.language.schemas import LanguageSchema
from app.language.services import LanguageService

router = APIRouter()


@router.get("/languages", response_model=List[LanguageSchema])
async def get_list_language(
    with_lessons: bool = Query(False, description="Отдавать только языки с уроками"),
    language_service: LanguageService = Depends(get_language_service),
    session: AsyncSession = Depends(get_session),
):
    return await language_service.get_list_without_pagination(
        session, with_lessons=with_lessons
    )
