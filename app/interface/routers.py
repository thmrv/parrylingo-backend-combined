from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database_async import get_session
from app.interface.dependencies import get_interface_service
from app.interface.schemas import InterfaceCreate, InterfaceSchema, InterfaceUpdate
from app.interface.services import InterfaceService

router = APIRouter(prefix="/admin")


@router.get("/interface", response_model=List[InterfaceSchema])
async def get_list(
    service: InterfaceService = Depends(get_interface_service),
    session: AsyncSession = Depends(get_session),
):
    return await service.get_list_without_pagination(session)


@router.get("/interface/{language_code}", response_model=InterfaceSchema)
async def get_single(
    language_code: str,
    service: InterfaceService = Depends(get_interface_service),
    session: AsyncSession = Depends(get_session),
):
    interface = await service.get_single(session, language_code=language_code)
    if not interface:
        raise HTTPException(status_code=404, detail="Interface not found")
    return interface


@router.post(
    "/interface", response_model=InterfaceSchema, status_code=status.HTTP_201_CREATED
)
async def create(
    data: InterfaceCreate,
    service: InterfaceService = Depends(get_interface_service),
    session: AsyncSession = Depends(get_session),
):
    return await service.create(session, data)


@router.patch("/interface/{language_code}", response_model=InterfaceSchema)
async def update(
    language_code: str,
    data: InterfaceUpdate,
    service: InterfaceService = Depends(get_interface_service),
    session: AsyncSession = Depends(get_session),
):
    interface = await service.update(session, data=data, language_code=language_code)
    if not interface:
        raise HTTPException(status_code=404, detail="Interface not found")
    return interface


@router.delete("/interface/{language_code}", response_model=InterfaceSchema)
async def delete(
    language_code: str,
    service: InterfaceService = Depends(get_interface_service),
    session: AsyncSession = Depends(get_session),
):
    return await service.delete(session, language_code=language_code)
