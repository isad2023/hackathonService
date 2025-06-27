from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from loguru import logger

from services.hackathon_service import HackathonService
from services.recommendations_service import RecommendationsService
from utils.jwt_utils import security, parse_jwt_token

hackathon_service = HackathonService()
recommendations_service = RecommendationsService()

hackathon_router = APIRouter(
    tags=["Hackathons"],
    responses={404: {"description": "Not Found"}},
)


class HackathonDto(BaseModel):
    id: UUID
    name: str
    task_description: Optional[str] = None
    end_of_registration: Optional[datetime] = None
    start_of_hack: Optional[datetime] = None
    end_of_hack: Optional[datetime] = None
    amount_money: Optional[float] = None
    type: Optional[str] = None
    city: Optional[str] = None
    approved: bool = None
    url: Optional[str] = None
    url_image: Optional[str] = None


class HackathonGetAllResponse(BaseModel):
    hackathons: List[HackathonDto]


class HackathonCreatePostRequest(BaseModel):
    name: str
    task_description: Optional[str] = None
    end_of_registration: Optional[datetime] = None
    start_of_hack: Optional[datetime] = None
    end_of_hack: Optional[datetime] = None
    amount_money: Optional[float] = None
    type: Optional[str] = None
    city: Optional[str] = None
    approved: bool = None
    url: Optional[str] = None
    url_image: Optional[str] = None


class HackathonCreatePostResponse(BaseModel):
    id: UUID


class HackathonGetByIdResponse(BaseModel):
    id: UUID
    name: str
    task_description: Optional[str] = None
    end_of_registration: Optional[datetime] = None
    start_of_hack: Optional[datetime] = None
    end_of_hack: Optional[datetime] = None
    amount_money: Optional[float] = None
    type: Optional[str] = None
    city: Optional[str] = None
    approved: bool = None
    url: Optional[str] = None
    url_image: Optional[str] = None


class HackathonPreparationResourcesResponse(BaseModel):
    hackathon_id: UUID
    hackathon_name: str
    resources: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@hackathon_router.get("/all", response_model=HackathonGetAllResponse)
async def get_all_hackathons():
    """
    Получить список всех хакатонов.
    """
    logger.info("hackathon_get_all")
    hackathons = await hackathon_service.get_all_hackathons()

    return HackathonGetAllResponse(
        hackathons=[
            HackathonDto(
                id=hackathon.id,
                name=hackathon.name,
                task_description=hackathon.task_description,
                end_of_registration=hackathon.end_of_registration,
                start_of_hack=hackathon.start_of_hack,
                end_of_hack=hackathon.end_of_hack,
                amount_money=hackathon.amount_money,
                type=hackathon.type,
                city=hackathon.city,
                approved=hackathon.approved,
                url=hackathon.url,
                url_image=hackathon.url_image,
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
        end_of_registration=request.end_of_registration,
        start_of_hack=request.start_of_hack,
        end_of_hack=request.end_of_hack,
        amount_money=request.amount_money,
        type=request.type,
        city=request.city,
        approved=request.approved,
        url=request.url,
        url_image=request.url_image,
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
    hackathon = await hackathon_service.get_hackathon_by_id(hackathon_id)

    if not hackathon:
        logger.error(f"hackathon_get_by_id: {hackathon_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Хакатон не найден")

    return HackathonGetByIdResponse(
        id=hackathon.id,
        name=hackathon.name,
        task_description=hackathon.task_description,
        end_of_registration=hackathon.end_of_registration,
        start_of_hack=hackathon.start_of_hack,
        end_of_hack=hackathon.end_of_hack,
        amount_money=hackathon.amount_money,
        type=hackathon.type,
        city=hackathon.city,
        approved=hackathon.approved,
        url=hackathon.url,
        url_image=hackathon.url_image,
    )


@hackathon_router.get("/{hackathon_id}/preparation-resources", response_model=HackathonPreparationResourcesResponse)
async def get_hackathon_preparation_resources(
    hackathon_id: UUID
):
    """
    Получить ресурсы для подготовки к хакатону по его ID.
    Отправляет описание хакатона в внешний API и получает рекомендации по подготовке.
    """
    logger.info(f"hackathon_get_preparation_resources: {hackathon_id}")
    
    # Получаем информацию о хакатоне
    hackathon = await hackathon_service.get_hackathon_by_id(hackathon_id)
    
    if not hackathon:
        logger.error(f"hackathon_get_preparation_resources: {hackathon_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Хакатон не найден")
    
    # Проверяем, есть ли описание хакатона
    if not hackathon.task_description:
        logger.warning(f"hackathon_get_preparation_resources: {hackathon_id} has no description")
        return HackathonPreparationResourcesResponse(
            hackathon_id=hackathon.id,
            hackathon_name=hackathon.name,
            resources=None,
            error_message="У хакатона отсутствует описание для генерации рекомендаций"
        )
    
    # Получаем ресурсы для подготовки через внешний API
    resources = await recommendations_service.get_preparation_resources(hackathon.task_description)
    
    if resources is None:
        logger.error(f"hackathon_get_preparation_resources: failed to get resources for {hackathon_id}")
        return HackathonPreparationResourcesResponse(
            hackathon_id=hackathon.id,
            hackathon_name=hackathon.name,
            resources=None,
            error_message="Не удалось получить ресурсы для подготовки. Попробуйте позже."
        )
    
    logger.info(f"hackathon_get_preparation_resources: successfully got resources for {hackathon_id}")
    return HackathonPreparationResourcesResponse(
        hackathon_id=hackathon.id,
        hackathon_name=hackathon.name,
        resources=resources,
        error_message=None
    )

