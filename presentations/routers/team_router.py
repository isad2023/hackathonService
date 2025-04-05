import uuid
from typing import List

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from loguru import logger
from pydantic import BaseModel, Field
from uuid import UUID

from persistent.db.team import Team
from services.team_service import TeamService
from services.hacker_service import HackerService
from utils.jwt_utils import security, parse_jwt_token

team_service = TeamService()  # Создаём экземпляр TeamService

team_router = APIRouter(
    prefix="/team",
    tags=["Teams"],
    responses={404: {"description": "Not Found"}},
)


class TeamDto(BaseModel):
    id: UUID
    ownerID: UUID
    hackathon_id: UUID
    name: str
    max_size: int
    hacker_ids: List[UUID]  # Список ID хакеров, состоящих в команде


class TeamGetAllResponse(BaseModel):
    teams: List[TeamDto]


class TeamCreatePostRequest(BaseModel):
    name: str = Field(..., description="Team name")
    max_size: int = Field(..., description="Maximum team size")
    hackathon_id: UUID = Field(..., description="Hackathon ID")


class CreateTeamPostResponse(BaseModel):
    id: UUID


class AddHackerToTeamRequest(BaseModel):
    team_id: UUID


class AddHackerToTeamResponse(BaseModel):
    id: UUID
    ownerID: UUID
    hackathon_id: UUID
    name: str
    max_size: int
    hacker_ids: List[UUID]


class GetTeamByIdGetResponse(BaseModel):
    id: UUID
    ownerID: UUID
    hackathon_id: UUID
    name: str
    max_size: int
    hacker_ids: List[UUID]


@team_router.get("/", response_model=TeamGetAllResponse)
async def get_all(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Получить список всех команд.
    Requires authentication.
    """
    claims = parse_jwt_token(credentials)
    logger.info(f"team_get_all by user {claims.uid}")
    teams = await team_service.get_all_teams()

    return TeamGetAllResponse(
        teams=[
            TeamDto(
                id=team.id,
                ownerID=team.owner_id,
                hackathon_id=team.hackathon_id,
                name=team.name,
                max_size=team.max_size,
                hacker_ids=[hacker.id for hacker in team.hackers],
            )
            for team in teams
        ]
    )


@team_router.get("/hackathon/{hackathon_id}", response_model=TeamGetAllResponse)
async def get_teams_by_hackathon(
    hackathon_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Получить список всех команд по ID хакатона.
    Requires authentication.
    """
    claims = parse_jwt_token(credentials)
    logger.info(f"team_get_by_hackathon: {hackathon_id} by user {claims.uid}")
    
    teams = await team_service.get_teams_by_hackathon_id(hackathon_id)
    
    return TeamGetAllResponse(
        teams=[
            TeamDto(
                id=team.id,
                ownerID=team.owner_id,
                hackathon_id=team.hackathon_id,
                name=team.name,
                max_size=team.max_size,
                hacker_ids=[hacker.id for hacker in team.hackers],
            )
            for team in teams
        ]
    )


@team_router.post("/", response_model=CreateTeamPostResponse, status_code=201)
async def create(
    request: TeamCreatePostRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Создать команду.
    Requires authentication.
    """
    claims = parse_jwt_token(credentials)
    user_id = claims.uid
    
    # Получаем hacker_id по user_id
    hacker_service = HackerService()
    hacker, found = await hacker_service.get_hacker_by_user_id(user_id)
    
    if not found:
        # Если хакер не найден, создаем его автоматически
        logger.info(f"team_create: auto-creating hacker for user_id {user_id}")
        default_name = f"Hacker-{user_id}"
        hacker_id, success = await hacker_service.upsert_hacker(user_id, default_name)
        
        if not success or hacker_id is None:
            logger.error(f"team_create: failed to auto-create hacker for user_id {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось создать профиль хакера"
            )
    else:
        hacker_id = hacker.id
    
    logger.info(f"team_create: {request.name} for hackathon {request.hackathon_id} by user {user_id}")
    team_id, status_code = await team_service.create_team(hacker_id, request.name, request.max_size, request.hackathon_id)

    if status_code == -1:
        logger.error(f"team_create: invalid max_size {request.max_size}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="max_size должен быть больше 0")
    if status_code == -2:
        logger.error(f"team_create: team already exists")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Команда с таким владельцем и названием уже существует")
    if status_code == -3:
        logger.error(f"team_create: hackathon not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Хакатон не найден")

    return CreateTeamPostResponse(
        id=team_id,
    )


@team_router.post("/add_hacker", response_model=AddHackerToTeamResponse, status_code=201)
async def add_hacker_to_team(
    request: AddHackerToTeamRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Добавить текущего участника в команду по ID команды.
    Requires authentication.
    """
    claims = parse_jwt_token(credentials)
    user_id = claims.uid
    
    # Получаем hacker_id по user_id
    hacker_service = HackerService()
    hacker, found = await hacker_service.get_hacker_by_user_id(user_id)
    
    if not found:
        # Если хакер не найден, создаем его автоматически
        logger.info(f"team_add_hacker: auto-creating hacker for user_id {user_id}")
        default_name = f"Hacker-{user_id}"
        hacker_id, success = await hacker_service.upsert_hacker(user_id, default_name)
        
        if not success or hacker_id is None:
            logger.error(f"team_add_hacker: failed to auto-create hacker for user_id {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось создать профиль хакера"
            )
    else:
        hacker_id = hacker.id
    
    logger.info(f"team_add_hacker: {request.team_id} hacker_id={hacker_id} by user {user_id}")
    
    team, status_code = await team_service.add_hacker_to_team(request.team_id, hacker_id)
    
    if status_code == -1:
        logger.error(f"team_add_hacker: team {request.team_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Команда не найдена")
    if status_code == -2:
        logger.error(f"team_add_hacker: hacker {hacker_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Хакер не найден")
    if status_code == -3:
        logger.error(f"team_add_hacker: team {request.team_id} is full")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Команда заполнена")
    if status_code == -4:
        logger.error(f"team_add_hacker: hacker {hacker_id} already in team")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Хакер уже в команде")
    if status_code < 0:
        logger.error(f"team_add_hacker: unknown error {status_code}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не удалось добавить хакера")

    return AddHackerToTeamResponse(
        id=team.id,
        ownerID=team.owner_id,
        hackathon_id=team.hackathon_id,
        name=team.name,
        max_size=team.max_size,
        hacker_ids=[hacker.id for hacker in team.hackers],
    )


@team_router.get("/my-teams", response_model=TeamGetAllResponse)
async def get_my_teams(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Получить список команд текущего пользователя.
    Возвращает все команды, в которых пользователь является участником.
    Requires authentication.
    """
    claims = parse_jwt_token(credentials)
    user_id = claims.uid
    logger.info(f"team_get_my_teams by user {user_id}")
    
    teams = await team_service.get_teams_by_user_id(user_id)
    
    return TeamGetAllResponse(
        teams=[
            TeamDto(
                id=team.id,
                ownerID=team.owner_id,
                hackathon_id=team.hackathon_id,
                name=team.name,
                max_size=team.max_size,
                hacker_ids=[hacker.id for hacker in team.hackers],
            )
            for team in teams
        ]
    )


@team_router.get("/{team_id}", response_model=GetTeamByIdGetResponse)
async def get_by_id(
    team_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Получить информацию о команде по её ID.
    Requires authentication.
    """
    claims = parse_jwt_token(credentials)
    logger.info(f"team_get_by_id: {team_id} by user {claims.uid}")
    team, found = await team_service.get_team_by_id(team_id)

    if not found:
        logger.error(f"team_get_by_id: {team_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Команда не найдена")

    return GetTeamByIdGetResponse(
        id=team.id,
        ownerID=team.owner_id,
        hackathon_id=team.hackathon_id,
        name=team.name,
        max_size=team.max_size,
        hacker_ids=[hacker.id for hacker in team.hackers],
    )
