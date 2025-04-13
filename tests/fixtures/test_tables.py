"""
Определения таблиц для тестирования.
Создает таблицы SQLite из моделей SQLAlchemy без схемы PostgreSQL.
"""
from sqlalchemy import MetaData, inspect, Column, Text, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from uuid import UUID as PythonUUID

# Импортируем модели из приложения
from persistent.db.base import Base
from persistent.db.team import Team
from persistent.db.hacker import Hacker
from persistent.db.hackathon import Hackathon
from persistent.db.role import Role
from persistent.db.winner_solution import WinnerSolution

# Создаем тестовые метаданные без схемы
test_metadata = MetaData()

# Клонируем таблицы из моделей в новые метаданные
def clone_tables_to_metadata():
    """Клонирует таблицы из существующих моделей SQLAlchemy в тестовые метаданные без схемы"""
    
    # Сначала клонируем все таблицы, чтобы они были зарегистрированы в метаданных
    for table_name, table in Base.metadata.tables.items():
        # Убираем схему 'public' из имени таблицы
        table_name_without_schema = table_name.split('.')[-1]
        # Клонируем таблицу без изменений
        new_table = table.to_metadata(test_metadata, schema=None)
    
    # Теперь заменяем типы колонок UUID на Text
    for table in test_metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, UUID):
                column.type = Text()
    
    # Получаем ссылки на таблицы для удобства использования в тестах
    result = {}
    table_list = list(test_metadata.tables.values())
    
    for table in table_list:
        table_name = table.name
        if table_name == "team":
            result["team_table"] = table
        elif table_name == "hackathon":
            result["hackathon_table"] = table
        elif table_name == "hacker":
            result["hacker_table"] = table
        elif table_name == "role":
            result["role_table"] = table
        elif table_name == "hacker_team_association":
            result["hacker_team_association"] = table
        elif table_name == "hacker_role_association":
            result["hacker_role_association"] = table
        elif table_name == "winner_solution":
            result["winner_solution"] = table
    
    return result

# Создаем таблицы один раз при импорте модуля
tables = clone_tables_to_metadata()

# Экспортируем таблицы для использования в тестах
team_table = tables["team_table"]
hackathon_table = tables["hackathon_table"]
hacker_table = tables["hacker_table"]
role_table = tables["role_table"]
hacker_team_association = tables["hacker_team_association"]
hacker_role_association = tables["hacker_role_association"]
winner_solution = tables["winner_solution"]

# Функция для преобразования UUID в строки (необходимо для SQLite)
def uuid_to_str(value):
    """Преобразует UUID в строку для SQLite"""
    if isinstance(value, PythonUUID):
        return str(value)
    return value

# Функция для создания тестовой БД
async def create_test_db():
    """Создает тестовую базу данных SQLite в памяти из моделей SQLAlchemy"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    
    # Создаем таблицы из тестовых метаданных
    async with engine.begin() as conn:
        await conn.run_sync(test_metadata.create_all)
    
    # Создаем фабрику сессий
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    return engine, session_factory 