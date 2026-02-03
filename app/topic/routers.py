from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database_async import get_session
from app.topic.dependencies import get_topic_service
from app.topic.schemas import TopicCreate, TopicSchema, TopicUpdate
from app.topic.services import TopicService

admin_router = APIRouter(prefix="/admin")


@admin_router.get("/topic", response_model=List[TopicSchema])
async def get_list(
    service: TopicService = Depends(get_topic_service),
    session: AsyncSession = Depends(get_session),
):
    return await service.get_list_without_pagination(session)


@admin_router.get("/topic/{topic_id}", response_model=TopicSchema)
async def get_single(
    topic_id: str,
    service: TopicService = Depends(get_topic_service),
    session: AsyncSession = Depends(get_session),
):
    topic = await service.get_single(session, id=topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@admin_router.post(
    "/topic", response_model=TopicSchema, status_code=status.HTTP_201_CREATED
)
async def create(
    data: TopicCreate,
    service: TopicService = Depends(get_topic_service),
    session: AsyncSession = Depends(get_session),
):
    return await service.create(session, data)


@admin_router.patch("/topic/{topic_id}", response_model=TopicSchema)
async def update(
    topic_id: str,
    data: TopicUpdate,
    service: TopicService = Depends(get_topic_service),
    session: AsyncSession = Depends(get_session),
):
    topic = await service.update(session, data=data, id=topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@admin_router.delete("/topic/{topic_id}", response_model=TopicSchema)
async def delete(
    topic_id: str,
    service: TopicService = Depends(get_topic_service),
    session: AsyncSession = Depends(get_session),
):
    topic = await service.delete(session, id=topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic
