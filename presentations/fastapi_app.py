from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Path, Response, status
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel

from presentations.routers.hackathon_router_mock import hackathon_router_mock
from presentations.routers.role_router import role_router
from presentations.routers.hackathon_router import hackathon_router
from presentations.routers.hacker_router import hacker_router
from presentations.routers.winner_solution_router import winner_solution_router

from services.mock_data_service import MockDataService
from services.scheduler_service import SchedulerService

# Глобальный экземпляр планировщика
scheduler_service = SchedulerService()

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
    
    # Запуск планировщика для парсинга хакатонов
    await scheduler_service.start_scheduler()
    logger.info("Scheduler service started successfully")

    yield  # Возвращаем управление приложению

    # Остановка планировщика при завершении приложения
    await scheduler_service.stop_scheduler()
    logger.info("Application shutdown: cleaning up...")


# Создание приложения FastAPI с lifespan
app = FastAPI(
    title="Сервис хакатонов",
    description="Сервис для работы со списком хакатонов, хакатонщиков и победителей",
    lifespan=lifespan,
    docs_url="/hackathons/docs",
    redoc_url="/hackathons/redoc",
    openapi_url="/hackathons/openapi.json",
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все источники для разработки - в продакшн лучше ограничить
    allow_credentials=False,
    allow_methods=["*"],  # Разрешить все HTTP-методы
    allow_headers=["*"],  # Разрешить все заголовки
)

#app.include_router(hackathon_router_mock, prefix="/hackathons")
app.include_router(hacker_router, prefix="/hackathons")
app.include_router(role_router, prefix="/hackathons")
app.include_router(hackathon_router, prefix="/hackathons")
app.include_router(winner_solution_router, prefix="/hackathons")
