from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from loguru import logger

from services.hackathon_service import HackathonService
from utils.jwt_utils import security, parse_jwt_token

hackathon_service = HackathonService()

hackathon_router = APIRouter(
    prefix="/hackathon",
    tags=["Hackathons"],
    responses={404: {"description": "Not Found"}},
)


class HackathonDto(BaseModel):
    id: UUID
    name: str
    task_description: Optional[str] = None
    start_of_registration: Optional[datetime] = None
    end_of_registration: Optional[datetime] = None
    start_of_hack: Optional[datetime] = None
    end_of_hack: Optional[datetime] = None
    amount_money: Optional[float] = None
    type: Optional[str] = None
    url: Optional[str] = None


class HackathonGetAllResponse(BaseModel):
    hackathons: List[HackathonDto]


class HackathonCreatePostRequest(BaseModel):
    name: str
    task_description: Optional[str] = None
    start_of_registration: Optional[datetime] = None
    end_of_registration: Optional[datetime] = None
    start_of_hack: Optional[datetime] = None
    end_of_hack: Optional[datetime] = None
    amount_money: Optional[float] = None
    type: Optional[str] = None
    url: Optional[str] = None


class HackathonCreatePostResponse(BaseModel):
    id: UUID


class HackathonGetByIdResponse(BaseModel):
    id: UUID
    name: str
    task_description: Optional[str] = None
    start_of_registration: Optional[datetime] = None
    end_of_registration: Optional[datetime] = None
    start_of_hack: Optional[datetime] = None
    end_of_hack: Optional[datetime] = None
    amount_money: Optional[float] = None
    type: Optional[str] = None
    url: Optional[str] = None


@hackathon_router.get("/", response_model=HackathonGetAllResponse)
async def get_all_hackathons(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Получить список всех хакатонов.
    Requires authentication.
    """
    claims = parse_jwt_token(credentials)
    logger.info(f"hackathon_get_all by user {claims.uid}")
    hackathons = await hackathon_service.get_all_hackathons()

    return HackathonGetAllResponse(
        hackathons=[
            HackathonDto(
                id=hackathon.id,
                name=hackathon.name,
                task_description=hackathon.task_description,
                start_of_registration=hackathon.start_of_registration,
                end_of_registration=hackathon.end_of_registration,
                start_of_hack=hackathon.start_of_hack,
                end_of_hack=hackathon.end_of_hack,
                amount_money=hackathon.amount_money,
                type=hackathon.type,
                url=hackathon.url,
            )
            for hackathon in hackathons
        ]
    )


@hackathon_router.post("/", response_model=HackathonCreatePostResponse, status_code=201)
async def upsert_hackathon(
    request: HackathonCreatePostRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Создать или обновить новый хакатон.
    Requires authentication.
    """
    claims = parse_jwt_token(credentials)
    logger.info(f"hackathon_post: {request.name} by user {claims.uid}")
    hackathon_id = await hackathon_service.upsert_hackathon(
        name=request.name,
        task_description=request.task_description,
        start_of_registration=request.start_of_registration,
        end_of_registration=request.end_of_registration,
        start_of_hack=request.start_of_hack,
        end_of_hack=request.end_of_hack,
        amount_money=request.amount_money,
        type=request.type,
        url=request.url,
    )

    return HackathonCreatePostResponse(id=hackathon_id)


@hackathon_router.get("/{hackathon_id}", response_model=HackathonGetByIdResponse)
async def get_hackathon_by_id(
    hackathon_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Получить информацию о хакатоне по ID.
    Requires authentication.
    """
    claims = parse_jwt_token(credentials)
    logger.info(f"hackathon_get_by_id: {hackathon_id} by user {claims.uid}")
    hackathon, found = await hackathon_service.get_hackathon_by_id(hackathon_id)

    if not found:
        logger.error(f"hackathon_get_by_id: {hackathon_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Хакатон не найден")

    return HackathonGetByIdResponse(
        id=hackathon.id,
        name=hackathon.name,
        task_description=hackathon.task_description,
        start_of_registration=hackathon.start_of_registration,
        end_of_registration=hackathon.end_of_registration,
        start_of_hack=hackathon.start_of_hack,
        end_of_hack=hackathon.end_of_hack,
        amount_money=hackathon.amount_money,
        type=hackathon.type,
        url=hackathon.url,
    )

