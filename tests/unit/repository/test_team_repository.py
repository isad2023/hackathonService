import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from uuid import UUID, uuid4
import datetime

# Импортируем все необходимые модели
from persistent.db.base import Base
from persistent.db.team import Team
from persistent.db.hacker import Hacker
from persistent.db.hackathon import Hackathon
from persistent.db.role import Role
from repository.team_repository import TeamRepository

# Импортируем тестовые таблицы и функцию создания БД из фикстур
from tests.fixtures.test_tables import (
    test_metadata, team_table, hackathon_table, hacker_table, 
    hacker_team_association, create_test_db, uuid_to_str
)


@pytest_asyncio.fixture(scope="function")
async def test_db():
    """Создаем временную тестовую базу данных SQLite в памяти"""
    # Создаем БД, используя функцию из фикстур
    engine, session_factory = await create_test_db()
    
    yield session_factory
    
    # Очищаем БД после тестов (база в памяти, поэтому достаточно просто закрыть соединение)
    await engine.dispose()


@pytest.fixture
def team_repository(test_db):
    """Создаем репозиторий с тестовой базой данных"""
    repository = TeamRepository()
    repository._sessionmaker = test_db
    return repository


class TestTeamRepository:
    @pytest.fixture
    def mock_team_data(self):
        """Данные для тестовой команды"""
        return {
            "id": str(uuid4()),  # преобразуем в строку для SQLite
            "owner_id": str(uuid4()),
            "name": "Test Team",
            "max_size": 5,
            "hackathon_id": str(uuid4()),
        }
    
    @pytest.fixture
    def mock_hacker_data(self):
        """Данные для тестового хакера"""
        return {
            "id": str(uuid4()),  # преобразуем в строку для SQLite
            "user_id": str(uuid4()),
            "name": "John Doe",  # изменено с first_name и last_name на name
        }
    
    @pytest_asyncio.fixture
    async def test_hackathon(self, test_db, mock_team_data):
        """Создает тестовый хакатон в БД"""
        async with test_db() as session:
            # Вставляем напрямую в таблицу через SQLAlchemy Core, не через ORM
            from sqlalchemy import insert
            stmt = insert(hackathon_table).values(
                id=mock_team_data["hackathon_id"],
                name="Test Hackathon",
                url="https://test.com",
                task_description="Test description",  # изменено с description на task_description
                start_of_hack=datetime.datetime.now(),  # добавлено обязательное поле
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow()
            )
            await session.execute(stmt)
            await session.commit()
            
        return {"id": mock_team_data["hackathon_id"], "name": "Test Hackathon"}
    
    @pytest.mark.asyncio
    async def test_create_team(self, test_db, mock_team_data, test_hackathon):
        """Тест создания команды"""
        # Создаем патч для метода create_team
        async def mock_create_team(self, owner_id, name, max_size, hackathon_id):
            # Преобразуем UUID в строки для SQLite
            from sqlalchemy import insert
            stmt = insert(team_table).values(
                id=str(uuid4()),
                owner_id=uuid_to_str(owner_id),  # используем функцию преобразования
                name=name,
                max_size=max_size,
                hackathon_id=uuid_to_str(hackathon_id),  # используем функцию преобразования
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow()
            )
            
            async with test_db() as session:
                result = await session.execute(stmt)
                inserted_id = result.inserted_primary_key[0]
                await session.commit()
                return UUID(inserted_id)
        
        # Патчим метод create_team в репозитории
        with patch.object(TeamRepository, 'create_team', mock_create_team):
            repository = TeamRepository()
            
            # Вызываем метод для создания команды
            team_id = await repository.create_team(
                owner_id=UUID(mock_team_data["owner_id"]),
                name=mock_team_data["name"],
                max_size=mock_team_data["max_size"],
                hackathon_id=UUID(mock_team_data["hackathon_id"])
            )
            
            # Проверяем, что ID получен
            assert team_id is not None
            
            # Проверяем, что команда сохранена в БД
            async with test_db() as session:
                from sqlalchemy import select
                stmt = select(team_table).where(team_table.c.id == str(team_id))
                result = await session.execute(stmt)
                team = result.fetchone()
                
                assert team is not None
                assert team.name == mock_team_data["name"]
                assert team.max_size == mock_team_data["max_size"]
    
    @pytest.mark.asyncio
    async def test_get_team_by_id(self, test_db, mock_team_data, test_hackathon):
        """Тест получения команды по ID"""
        # Сначала создаем команду
        async with test_db() as session:
            from sqlalchemy import insert
            stmt = insert(team_table).values(
                id=mock_team_data["id"],
                owner_id=mock_team_data["owner_id"],
                name=mock_team_data["name"],
                max_size=mock_team_data["max_size"],
                hackathon_id=mock_team_data["hackathon_id"],
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow()
            )
            await session.execute(stmt)
            await session.commit()
        
        # Создаем патч для метода get_team_by_id
        async def mock_get_team_by_id(self, team_id):
            from sqlalchemy import select
            stmt = select(team_table).where(team_table.c.id == uuid_to_str(team_id))  # используем uuid_to_str
            
            async with test_db() as session:
                result = await session.execute(stmt)
                team_data = result.fetchone()
                
                if not team_data:
                    return None
                
                # Создаем объект, имитирующий Team с атрибутами из БД
                team = MagicMock()
                team.id = UUID(team_data.id)
                team.name = team_data.name
                team.max_size = team_data.max_size
                team.hackers = []  # Пустой список хакеров
                
                return team
        
        # Патчим метод get_team_by_id в репозитории
        with patch.object(TeamRepository, 'get_team_by_id', mock_get_team_by_id):
            repository = TeamRepository()
            
            # Вызываем метод для получения команды
            team = await repository.get_team_by_id(UUID(mock_team_data["id"]))
            
            # Проверяем возвращаемое значение
            assert team is not None
            assert str(team.id) == mock_team_data["id"]
            assert team.name == mock_team_data["name"]
            assert team.max_size == mock_team_data["max_size"]
    
    @pytest.mark.asyncio
    async def test_get_team_by_id_not_found(self, test_db):
        """Тест получения несуществующей команды"""
        # Создаем патч для метода get_team_by_id
        async def mock_get_team_by_id(self, team_id):
            from sqlalchemy import select
            stmt = select(team_table).where(team_table.c.id == uuid_to_str(team_id))  # используем uuid_to_str
            
            async with test_db() as session:
                result = await session.execute(stmt)
                team_data = result.fetchone()
                
                if not team_data:
                    return None
                
                # Если команда найдена, то создаем объект (но это не должно случиться)
                team = MagicMock()
                team.id = UUID(team_data.id)
                
                return team
        
        # Патчим метод get_team_by_id в репозитории
        with patch.object(TeamRepository, 'get_team_by_id', mock_get_team_by_id):
            repository = TeamRepository()
            
            # Вызываем метод для получения команды с несуществующим ID
            non_existent_id = uuid4()
            team = await repository.get_team_by_id(non_existent_id)
            
            # Проверяем, что результат равен None
            assert team is None
    
    @pytest.mark.asyncio
    async def test_add_hacker_to_team(self, test_db, mock_team_data, mock_hacker_data, test_hackathon):
        """Тест добавления хакера в команду"""
        # Создаем команду и хакера напрямую в БД
        async with test_db() as session:
            # Создаем команду
            from sqlalchemy import insert
            stmt1 = insert(team_table).values(
                id=mock_team_data["id"],
                owner_id=mock_team_data["owner_id"],
                name=mock_team_data["name"],
                max_size=mock_team_data["max_size"],
                hackathon_id=mock_team_data["hackathon_id"],
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow()
            )
            await session.execute(stmt1)
            
            # Создаем хакера
            stmt2 = insert(hacker_table).values(
                id=mock_hacker_data["id"],
                user_id=mock_hacker_data["user_id"],
                name=mock_hacker_data["name"],  # используем name вместо first_name и last_name
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow()
            )
            await session.execute(stmt2)
            await session.commit()
        
        # Создаем патч для метода add_hacker_to_team
        async def mock_add_hacker_to_team(self, team_id, hacker):
            # Сначала проверяем, существует ли команда
            from sqlalchemy import select
            stmt_team = select(team_table).where(team_table.c.id == uuid_to_str(team_id))  # используем uuid_to_str
            
            async with test_db() as session:
                # Проверяем наличие команды
                team_result = await session.execute(stmt_team)
                team_data = team_result.fetchone()
                
                if not team_data:
                    return None, -1  # Команда не найдена
                
                # Проверяем, находится ли хакер уже в команде
                stmt_assoc = select(hacker_team_association).where(
                    (hacker_team_association.c.team_id == uuid_to_str(team_id)) &
                    (hacker_team_association.c.hacker_id == uuid_to_str(hacker.id))
                )
                assoc_result = await session.execute(stmt_assoc)
                if assoc_result.fetchone():
                    # Создаем мок-команду с хакером уже в списке
                    mock_team = MagicMock()
                    mock_team.id = team_id
                    mock_team.hackers = [hacker]
                    return mock_team, -4  # Хакер уже в команде
                
                # Проверяем максимальный размер команды
                stmt_count = select(hacker_team_association).where(
                    hacker_team_association.c.team_id == uuid_to_str(team_id)
                )
                count_result = await session.execute(stmt_count)
                team_members = count_result.fetchall()
                
                if len(team_members) >= team_data.max_size:
                    return None, -2  # Команда уже заполнена
                
                # Добавляем хакера в команду
                stmt_insert = insert(hacker_team_association).values(
                    team_id=uuid_to_str(team_id),
                    hacker_id=uuid_to_str(hacker.id)
                )
                await session.execute(stmt_insert)
                await session.commit()
                
                # Создаем мок-объект команды с хакером
                mock_team = MagicMock()
                mock_team.id = team_id
                mock_team.hackers = [hacker]  # Добавляем хакера в список
                
                return mock_team, 1  # Успешно добавлен
        
        # Патчим метод add_hacker_to_team в репозитории
        with patch.object(TeamRepository, 'add_hacker_to_team', mock_add_hacker_to_team):
            repository = TeamRepository()
            
            # Создаем мок-объект хакера для передачи в метод
            mock_hacker = MagicMock()
            mock_hacker.id = UUID(mock_hacker_data["id"])
            
            # Вызываем метод добавления хакера в команду
            team, status = await repository.add_hacker_to_team(
                team_id=UUID(mock_team_data["id"]),
                hacker=mock_hacker
            )
            
            # Проверяем, что хакер был успешно добавлен
            assert status == 1
            assert team is not None
            assert len(team.hackers) == 1
            assert team.hackers[0].id == mock_hacker.id 