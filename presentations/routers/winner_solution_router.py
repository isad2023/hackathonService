from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from loguru import logger
from pydantic import BaseModel

from services.winner_solution_service import WinnerSolutionService
from utils.jwt_utils import security, parse_jwt_token

winner_solution_service = WinnerSolutionService()

winner_solution_router = APIRouter(
    prefix="/winner-solution",
    tags=["Winner Solutions"],
    responses={404: {"description": "Not Found"}},
)


class WinnerSolutionDto(BaseModel):
    id: UUID
    win_money: float
    link_to_solution: str
    link_to_presentation: str
    can_share: bool
    hackathon_id: UUID
    team_id: UUID


class WinnerSolutionGetAllResponse(BaseModel):
    winner_solutions: List[WinnerSolutionDto]


class WinnerSolutionCreateRequest(BaseModel):
    win_money: float
    link_to_solution: str
    link_to_presentation: str
    can_share: bool
    hackathon_id: UUID
    team_id: UUID


class WinnerSolutionCreateResponse(BaseModel):
    id: UUID


class WinnerSolutionGetByIdResponse(BaseModel):
    id: UUID
    win_money: float
    link_to_solution: str
    link_to_presentation: str
    can_share: bool
    hackathon_id: UUID
    team_id: UUID


@winner_solution_router.get("/all", response_model=WinnerSolutionGetAllResponse)
async def get_all(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Получить список всех призерских решений.
    Requires authentication.
    """
    claims = parse_jwt_token(credentials)
    logger.info(f"winner_solution_get_all by user {claims.uid}")
    winner_solutions = await winner_solution_service.get_all_winner_solutions()
    
    return WinnerSolutionGetAllResponse(
        winner_solutions=[
            WinnerSolutionDto(
                id=solution.id,
                win_money=solution.win_money,
                link_to_solution=solution.link_to_solution,
                link_to_presentation=solution.link_to_presentation,
                can_share=solution.can_share,
                hackathon_id=solution.hackathon_id,
                team_id=solution.team_id,
            )
            for solution in winner_solutions
        ]
    )


@winner_solution_router.post("/", response_model=WinnerSolutionCreateResponse, status_code=201)
async def create(
    request: WinnerSolutionCreateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Создать призерское решение.
    Requires authentication.
    """
    claims = parse_jwt_token(credentials)
    logger.info(f"winner_solution_create: team {request.team_id} for hackathon {request.hackathon_id} by user {claims.uid}")
    solution_id, success = await winner_solution_service.create_winner_solution(
        hackathon_id=request.hackathon_id,
        team_id=request.team_id,
        win_money=request.win_money,
        link_to_solution=request.link_to_solution,
        link_to_presentation=request.link_to_presentation,
        can_share=request.can_share,
    )
    
    if not success:
        logger.error(f"winner_solution_create: solution already exists for team {request.team_id}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Решение от этой команды уже записано")
    
    return WinnerSolutionCreateResponse(
        id=solution_id,
    )


@winner_solution_router.get("/{solution_id}", response_model=WinnerSolutionGetByIdResponse)
async def get_by_id(
    solution_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Получить призерское решение по ID.
    Requires authentication.
    """
    claims = parse_jwt_token(credentials)
    logger.info(f"winner_solution_get_by_id: {solution_id} by user {claims.uid}")
    solution, found = await winner_solution_service.get_winner_solution_by_id(solution_id)
    
    if not found:
        logger.error(f"winner_solution_get_by_id: {solution_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Решение не найдено")
    
    return WinnerSolutionGetByIdResponse(
        id=solution.id,
        win_money=solution.win_money,
        link_to_solution=solution.link_to_solution,
        link_to_presentation=solution.link_to_presentation,
        can_share=solution.can_share,
        hackathon_id=solution.hackathon_id,
        team_id=solution.team_id,
    )