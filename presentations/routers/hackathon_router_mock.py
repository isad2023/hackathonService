from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from loguru import logger

from utils.jwt_utils import security, parse_jwt_token

hackathon_router_mock = APIRouter(
    tags=["Hackathons Mock"],
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
    city: Optional[str] = None
    approved: bool = None
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
    city: Optional[str] = None
    approved: bool = None
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
    city: Optional[str] = None
    approved: bool = None
    url: Optional[str] = None


@hackathon_router_mock.get("/all", response_model=HackathonGetAllResponse)
async def get_all_hackathons():
    """
    Получить список всех хакатонов (mock version).
    Requires authentication.
    """
    
    # Возвращаем статичные моковые данные
    mock_hackathons = [
        HackathonDto(
            id=UUID("123e4567-e89b-12d3-a456-426614174000"),
            name="AI Hackathon 2024",
            task_description="Разработка AI-решений для автоматизации бизнес-процессов",
            start_of_registration=datetime(2024, 1, 1, 10, 0),
            end_of_registration=datetime(2024, 1, 15, 23, 59),
            start_of_hack=datetime(2024, 1, 20, 10, 0),
            end_of_hack=datetime(2024, 1, 22, 18, 0),
            amount_money=100000.0,
            type="online",
            city="Moscow",
            approved=True,
            url="https://example.com/ai-hackathon-2024"
        ),
        HackathonDto(
            id=UUID("223e4567-e89b-12d3-a456-426614174001"),
            name="Fintech Challenge",
            task_description="Создание инновационных финтех решений",
            start_of_registration=datetime(2024, 2, 1, 10, 0),
            end_of_registration=datetime(2024, 2, 15, 23, 59),
            start_of_hack=datetime(2024, 2, 20, 10, 0),
            end_of_hack=datetime(2024, 2, 22, 18, 0),
            amount_money=50000.0,
            type="offline",
            city="Saint Petersburg",
            approved=True,
            url="https://example.com/fintech-challenge"
        ),
        HackathonDto(
            id=UUID("323e4567-e89b-12d3-a456-426614174002"),
            name="Green Tech Hackathon",
            task_description="Разработка экологически чистых технологических решений",
            start_of_registration=datetime(2024, 3, 1, 10, 0),
            end_of_registration=datetime(2024, 3, 15, 23, 59),
            start_of_hack=datetime(2024, 3, 20, 10, 0),
            end_of_hack=datetime(2024, 3, 22, 18, 0),
            amount_money=75000.0,
            type="hybrid",
            city="Novosibirsk",
            approved=False,
            url="https://example.com/green-tech-hackathon"
        )
    ]
    
    return HackathonGetAllResponse(hackathons=mock_hackathons)


@hackathon_router_mock.post("/", response_model=HackathonCreatePostResponse, status_code=201)
async def upsert_hackathon(
    request: HackathonCreatePostRequest
):
    """
    Создать или обновить новый хакатон (mock version).
    Requires authentication.
    """    
    # Всегда возвращаем один и тот же фиксированный ID
    fixed_mock_id = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    logger.info(f"hackathon_post_mock: returning fixed mock ID {fixed_mock_id}")
    
    return HackathonCreatePostResponse(id=fixed_mock_id)


@hackathon_router_mock.get("/{hackathon_id}", response_model=HackathonGetByIdResponse)
async def get_hackathon_by_id(
    hackathon_id: UUID
):
    """
    Получить информацию о хакатоне по ID (mock version).
    Requires authentication.
    """
    # Для известных ID возвращаем соответствующие данные
    if hackathon_id == UUID("123e4567-e89b-12d3-a456-426614174000"):
        return HackathonGetByIdResponse(
            id=UUID("123e4567-e89b-12d3-a456-426614174000"),
            name="AI Hackathon 2024",
            task_description="Разработка AI-решений для автоматизации бизнес-процессов",
            start_of_registration=datetime(2024, 1, 1, 10, 0),
            end_of_registration=datetime(2024, 1, 15, 23, 59),
            start_of_hack=datetime(2024, 1, 20, 10, 0),
            end_of_hack=datetime(2024, 1, 22, 18, 0),
            amount_money=100000.0,
            type="online",
            city="Moscow",
            approved=True,
            url="https://example.com/ai-hackathon-2024"
        )
    elif hackathon_id == UUID("223e4567-e89b-12d3-a456-426614174001"):
        return HackathonGetByIdResponse(
            id=UUID("223e4567-e89b-12d3-a456-426614174001"),
            name="Fintech Challenge",
            task_description="Создание инновационных финтех решений",
            start_of_registration=datetime(2024, 2, 1, 10, 0),
            end_of_registration=datetime(2024, 2, 15, 23, 59),
            start_of_hack=datetime(2024, 2, 20, 10, 0),
            end_of_hack=datetime(2024, 2, 22, 18, 0),
            amount_money=50000.0,
            type="offline",
            city="Saint Petersburg",
            approved=True,
            url="https://example.com/fintech-challenge"
        )
    elif hackathon_id == UUID("323e4567-e89b-12d3-a456-426614174002"):
        return HackathonGetByIdResponse(
            id=UUID("323e4567-e89b-12d3-a456-426614174002"),
            name="Green Tech Hackathon",
            task_description="Разработка экологически чистых технологических решений",
            start_of_registration=datetime(2024, 3, 1, 10, 0),
            end_of_registration=datetime(2024, 3, 15, 23, 59),
            start_of_hack=datetime(2024, 3, 20, 10, 0),
            end_of_hack=datetime(2024, 3, 22, 18, 0),
            amount_money=75000.0,
            type="hybrid",
            city="Novosibirsk",
            approved=False,
            url="https://example.com/green-tech-hackathon"
        )
    else:
        # Для любого другого ID возвращаем 404
        logger.error(f"hackathon_get_by_id_mock: {hackathon_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Хакатон не найден") 