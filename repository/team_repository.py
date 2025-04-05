from typing import Tuple, cast, List, Optional

from loguru import logger
from sqlalchemy.exc import IntegrityError

from infrastructure.db.connection import pg_connection
from persistent.db.hacker import Hacker
from persistent.db.team import Team
from sqlalchemy import ColumnElement, select, delete, UUID
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectinload


class TeamRepository:
    def __init__(self) -> None:
        self._sessionmaker = pg_connection()

    async def get_all_teams(self) -> List[Team]:
        """
        Получение всех команд из базы данных.
        """
        stmt = select(Team)

        async with self._sessionmaker() as session:
            resp = await session.execute(stmt)

            rows = resp.fetchall()  # Извлекаем все строки
            teams = [row[0] for row in rows]  # Преобразуем их в список объектов Hacker
            return teams

    async def create_team(self, owner_id: UUID, name: str, max_size: int, hackathon_id: UUID) -> Optional[UUID]:
        """
        Создание новой команды в базе данных.
        """
        stmt = insert(Team).values({
            "owner_id": owner_id,
            "name": name,
            "max_size": max_size,
            "hackathon_id": hackathon_id,
        })

        async with self._sessionmaker() as session:
            result = await session.execute(stmt)
            team_id = result.inserted_primary_key[0]

            try:
                await session.commit()
            except IntegrityError as error:
                await session.rollback()
                return None

        return team_id

    async def add_hacker_to_team(self, team_id: UUID, hacker: Hacker) -> Tuple[Optional[Team], int]:
        """
        Добавление участника в команду.

        :returns -1 Команда не найдена
        :returns -2 Команда уже заполнена
        :returns -4 Хакер уже в команде
        """
        async with self._sessionmaker() as session:
            # Загружаем только команду и хакеров, без других связанных объектов
            # Используем selectinload только для хакеров, чтобы избежать проблем с WinnerSolution
            stmt = select(Team).where(Team.id == team_id).options(
                selectinload(Team.hackers)
            ).limit(1)
            
            resp = await session.execute(stmt)
            row = resp.fetchone()
            
            if not row:
                return None, -1
                
            team = row[0]
            
            # Проверяем, находится ли хакер уже в команде
            hacker_ids = [h.id for h in team.hackers]
            if hacker.id in hacker_ids:
                logger.info(f"Хакер {hacker.id} уже в команде {team_id}")
                return team, -4
            
            if len(team.hackers) >= team.max_size:
                return None, -2
            
            # Получаем свежий объект хакера из этой сессии    
            hacker_stmt = select(Hacker).where(Hacker.id == hacker.id)
            hacker_result = await session.execute(hacker_stmt)
            hacker_obj = hacker_result.scalar_one_or_none()
            
            if not hacker_obj:
                logger.error(f"Хакер {hacker.id} не найден в сессии")
                return None, -2
                
            # Добавляем хакера к команде
            team.hackers.append(hacker_obj)
            
            # Аккуратно сохраняем изменения
            try:
                await session.commit()
                # Перезагружаем команду, чтобы получить обновленные данные
                session.expire(team)
                stmt = select(Team).where(Team.id == team_id).options(
                    selectinload(Team.hackers)
                ).limit(1)
                resp = await session.execute(stmt)
                row = resp.fetchone()
                return row[0] if row else None, 1
            except Exception as e:
                logger.error(f"Ошибка при добавлении хакера в команду: {str(e)}")
                await session.rollback()
                return None, -5

    async def get_team_by_id(self, team_id: UUID) -> Optional[Team]:
        """
        Получение команды по её идентификатору.
        """
        async with self._sessionmaker() as session:
            # Используем отдельную сессию для загрузки команды
            stmt = select(Team).where(Team.id == team_id).options(
                selectinload(Team.hackers)
            ).limit(1)
            
            resp = await session.execute(stmt)
            row = resp.fetchone()
            return row[0] if row else None

    async def get_team_by_name(self, name: str) -> Optional[Team]:
        """
        Получение команды по её имени.
        """
        async with self._sessionmaker() as session:
            # Используем отдельную сессию для загрузки команды
            stmt = select(Team).where(Team.name == name).options(
                selectinload(Team.hackers)
            ).limit(1)
            
            resp = await session.execute(stmt)
            row = resp.fetchone()
            return row[0] if row else None

    async def get_teams_by_hackathon_id(self, hackathon_id: UUID) -> List[Team]:
        """
        Получение всех команд, связанных с указанным хакатоном.
        """
        stmt = select(Team).where(Team.hackathon_id == hackathon_id).options(
            selectinload(Team.hackers)
        )
        
        async with self._sessionmaker() as session:
            resp = await session.execute(stmt)
            
            rows = resp.fetchall()
            teams = [row[0] for row in rows]
            return teams

    async def get_teams_by_user_id(self, user_id: UUID) -> List[Team]:
        """
        Получение всех команд, в которых пользователь с указанным user_id является участником.
        
        Ищет хакера по user_id и возвращает все команды, в которых он состоит.
        """
        async with self._sessionmaker() as session:
            # Сначала находим хакера по user_id
            hacker_stmt = select(Hacker).where(Hacker.user_id == user_id)
            hacker_result = await session.execute(hacker_stmt)
            hacker_row = hacker_result.scalar_one_or_none()
            
            if not hacker_row:
                logger.warning(f"Хакер с user_id={user_id} не найден")
                return []
            
            # Загружаем полную информацию о командах, включая связанных хакеров
            # Используем join для более эффективного запроса
            from persistent.db.relations import hacker_team_association
            
            teams_stmt = (
                select(Team)
                .join(hacker_team_association, Team.id == hacker_team_association.c.team_id)
                .where(hacker_team_association.c.hacker_id == hacker_row.id)
                .options(selectinload(Team.hackers))
            )
            
            teams_result = await session.execute(teams_stmt)
            teams = [row[0] for row in teams_result.fetchall()]
            
            return teams
