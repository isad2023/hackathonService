import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from loguru import logger
from pydantic import BaseModel
from uuid import UUID

from persistent.db.team import Team
from persistent.db.role import RoleEnum
from services.hacker_service import HackerService
from utils.jwt_utils import security, parse_jwt_token, get_current_user_id

hacker_service = HackerService()  # Создаём экземпляр RoleService

hacker_router = APIRouter(
    prefix="/hacker",
    tags=["Hackers"],
    responses={404: {"description": "Not Found"}},
)


class HackerDto(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    roles: List[str]
    team_ids: List[UUID]


class HackerGetAllResponse(BaseModel):
    hackers: List[HackerDto]


class HackerCreatePostRequest(BaseModel):
    name: str
    role_ids: Optional[List[UUID]] = None


class CreateHackerPostResponse(BaseModel):
    id: UUID


class HackerAddRolesPostRequest(BaseModel):
    role_names: List[str]


class GetHackerByIdGetRequest(BaseModel):
    hacker_id: UUID


class GetHackerByIdGetResponse(BaseModel):
    user_id: UUID
    name: str
    roles: List[str]
    team_ids: List[UUID]


@hacker_router.get("/", response_model=HackerGetAllResponse)
async def get_all(user_id: str = Depends(get_current_user_id)):
    """
    Получить список всех хакатонщиков.
    Requires authentication.
    """
    logger.info(f"hacker_get_all by user {user_id}")
    hackers = await hacker_service.get_all_hackers()

    return HackerGetAllResponse(
        hackers=[
            HackerDto(id=hacker.id,
                      user_id=hacker.user_id,
                      name=hacker.name,
                      roles=[role.name for role in hacker.roles],
                      team_ids=[team.id for team in hacker.teams], )
            for hacker in hackers
        ]
    )


@hacker_router.post("/", response_model=CreateHackerPostResponse, status_code=201)
async def upsert(
    request: HackerCreatePostRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Создать или обновить хакатонщика.
    Requires authentication.
    """
    logger.info(f"hacker_post: {user_id} by user {user_id}")
    hacker_id, success = await hacker_service.upsert_hacker(user_id, request.name)
    
    if not success or hacker_id is None:
        logger.error(f"Failed to upsert hacker with user_id={user_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось создать или обновить хакатонщика"
        )
    
    # Если есть role_ids, добавляем их к хакеру
    if request.role_ids:
        roles_success = await hacker_service.update_hacker_roles_by_id(hacker_id, request.role_ids)
        if not roles_success:
            logger.warning(f"Failed to update roles for hacker_id={hacker_id}")

    return CreateHackerPostResponse(
        id=hacker_id,
    )


@hacker_router.post("/update_roles", status_code=201)
async def update_roles(
    request: HackerAddRolesPostRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Установить роли для текущего хакатонщика.
    Для определения хакатонщика используется user_id из токена авторизации.
    Requires authentication.
    """
    logger.info(f"hacker_update_roles: roles {request.role_names} for user {user_id}")
    success = await hacker_service.update_hacker_roles_by_user_id(user_id, request.role_names)
    
    if not success:
        logger.error(f"hacker_update_roles: failed to update roles for user {user_id}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не удалось обновить роли")


@hacker_router.get("/{hacker_id}", response_model=GetHackerByIdGetResponse)
async def get_by_id(
    hacker_id: UUID,
    user_id: str = Depends(get_current_user_id)
):
    """
    Получить хакатонщика по id.
    Requires authentication.
    """
    logger.info(f"hacker_get_by_id: {hacker_id} by user {user_id}")
    hacker, found = await hacker_service.get_hacker_by_id(hacker_id)

    if not found:
        logger.error(f"hacker_get_by_id: {hacker_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Хакер не найден")

    return GetHackerByIdGetResponse(
        user_id=hacker.user_id,
        name=hacker.name,
        roles=[role.name for role in hacker.roles],
        team_ids=[team.id for team in hacker.teams],
    )
