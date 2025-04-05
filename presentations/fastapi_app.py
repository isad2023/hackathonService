from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Path, Response, status
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel

from presentations.routers.role_router import role_router
from presentations.routers.hackathon_router import hackathon_router
from presentations.routers.hacker_router import hacker_router
from presentations.routers.team_router import team_router
from presentations.routers.winner_solution_router import winner_solution_router

from services.mock_data_service import MockDataService

# Lifespan-событие
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Обработчик жизненного цикла приложения.
    Используется для инициализации данных при старте и очистки ресурсов при завершении.
    """
    # Инициализация тестовых данных
    mock_data_service = MockDataService()
    await mock_data_service.initialize_mock_data()

    yield  # Возвращаем управление приложению

    logger.info("Application shutdown: cleaning up...")  # Действия при завершении приложения


# Создание приложения FastAPI с lifespan
app = FastAPI(
    title="Наше последнее приложение!",
    description="Прикольное приложение (последнее)",
    lifespan=lifespan,
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все источники для разработки - в продакшн лучше ограничить
    allow_credentials=False,
    allow_methods=["*"],  # Разрешить все HTTP-методы
    allow_headers=["*"],  # Разрешить все заголовки
)

app.include_router(hacker_router)
app.include_router(role_router)
app.include_router(team_router)
app.include_router(hackathon_router)
app.include_router(winner_solution_router)
