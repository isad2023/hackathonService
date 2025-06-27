from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from loguru import logger

from services.role_service import RoleService
from utils.jwt_utils import security, parse_jwt_token

role_service = RoleService()

role_router = APIRouter(
    prefix="/role",
    tags=["Roles"],
    responses={404: {"description": "Not Found"}},
)


class RoleDto(BaseModel):
    id: UUID
    name: str


class RoleGetAllResponse(BaseModel):
    roles: List[RoleDto]


@role_router.get("/all", response_model=RoleGetAllResponse)
async def get_all_roles(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Получить список всех ролей.
    Requires authentication.
    """
    claims = parse_jwt_token(credentials)
    logger.info(f"Запрос на получение списка всех ролей от пользователя {claims.uid}")
    
    try:
        roles = await role_service.get_all_roles()
        
        return RoleGetAllResponse(
            roles=[
                RoleDto(
                    id=role.id,
                    name=role.name
                )
                for role in roles
            ]
        )
        
    except Exception as e:
        logger.exception("Ошибка при получении списка ролей")
        raise HTTPException(
            status_code=500,
            detail="Внутренняя ошибка сервера"
        )