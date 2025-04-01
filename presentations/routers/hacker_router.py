import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from loguru import logger
from pydantic import BaseModel
from uuid import UUID

from persistent.db.team import Team
from persistent.db.role import RoleEnum
from services.hacker_service import HackerService
from utils.jwt_utils import security, parse_jwt_token

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
    user_id: UUID
    name: str


class CreateHackerPostResponse(BaseModel):
    id: UUID


class HackerAddRolesPostRequest(BaseModel):
    hacker_id: UUID
    role_names: List[str]


class GetHackerByIdGetRequest(BaseModel):
    hacker_id: UUID


class GetHackerByIdGetResponse(BaseModel):
    user_id: UUID
    name: str
    roles: List[str]
    team_ids: List[UUID]


@hacker_router.get("/", response_model=HackerGetAllResponse)
async def get_all(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Получить список всех хакатонщиков.
    Requires authentication.
    """
    claims = parse_jwt_token(credentials)
    logger.info(f"hacker_get_all by user {claims.uid}")
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
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Создать или обновить хакатонщика.
    Requires authentication.
    """
    claims = parse_jwt_token(credentials)
    logger.info(f"hacker_post: {request.user_id} by user {claims.uid}")
    hacker_id = await hacker_service.upsert_hacker(request.user_id, request.name)

    return CreateHackerPostResponse(
        id=hacker_id,
    )


@hacker_router.post("/update_roles", status_code=201)
async def update_roles(
    request: HackerAddRolesPostRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Установить роли хакатонщику.
    Requires authentication.
    """
    claims = parse_jwt_token(credentials)
    logger.info(f"hacker_update_roles: {request.hacker_id} {request.role_names} by user {claims.uid}")
    success = await hacker_service.update_hacker_roles(request.hacker_id, request.role_names)
    
    if not success:
        logger.error(f"hacker_update_roles: failed to update roles for hacker {request.hacker_id}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не удалось обновить роли")


@hacker_router.get("/{hacker_id}", response_model=GetHackerByIdGetResponse)
async def get_by_id(
    hacker_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Получить хакатонщика по id.
    Requires authentication.
    """
    claims = parse_jwt_token(credentials)
    logger.info(f"hacker_get_by_id: {hacker_id} by user {claims.uid}")
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
