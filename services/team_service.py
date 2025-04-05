from datetime import datetime
from typing import List, Optional, Tuple
from loguru import logger
from sqlalchemy import UUID

from infrastructure.db.connection import pg_connection
from persistent.db.team import Team
from repository.hacker_repository import HackerRepository
from repository.team_repository import TeamRepository
from repository.hackathon_repository import HackathonRepository


class TeamService:
    def __init__(self) -> None:
        self.team_repository = TeamRepository()
        self.hacker_repository = HackerRepository()
        self.hackathon_repository = HackathonRepository()

    async def get_all_teams(self) -> List[Team]:
        """
        Возвращает все команды.
        """
        teams = await self.team_repository.get_all_teams()

        if not teams:
            logger.warning("Команды не найдены.")
        return teams

    async def create_team(self, owner_id: UUID, name: str, max_size: int, hackathon_id: UUID) -> Tuple[Optional[UUID], int]:
        """
        Создаёт новую команду.

        :returns -1 max_size должен быть больше 0
        :returns -2 Команда с таким владельцем и названием уже существует
        :returns -3 Хакатон не найден
        """
        if max_size <= 0:
            logger.error(f"Неверный max_size: {max_size}, должен быть > 0")
            return None, -1

        # Проверяем, что хакатон существует
        hackathon = await self.hackathon_repository.get_hackathon_by_id(hackathon_id)
        if not hackathon:
            logger.error(f"Хакатон с id={hackathon_id} не найден")
            return None, -3

        # Создаем команду
        new_team_id = await self.team_repository.create_team(
            owner_id=owner_id,
            name=name,
            max_size=max_size,
            hackathon_id=hackathon_id,
        )

        if not new_team_id:
            logger.error(f"Не удалось создать команду. Возможно, уже существует.")
            return None, -2

        # Получаем хакера по ID
        hacker = await self.hacker_repository.get_hacker_by_id(owner_id)
        if not hacker:
            logger.error(f"Хакер с id={owner_id} не найден при добавлении в команду")
            return new_team_id, 1  # Команда создана, но без хакера
        
        # Добавляем хакера (владельца) в команду в отдельной транзакции
        team, status_code = await self.team_repository.add_hacker_to_team(new_team_id, hacker)
        if status_code < 0 and status_code != -4:  # -4 означает, что хакер уже в команде
            logger.warning(f"Не удалось добавить владельца в команду: {status_code}")
            # Но команду все равно считаем созданной
        
        return new_team_id, 1

    async def get_team_by_id(self, team_id: UUID) -> Tuple[Optional[Team], bool]:
        """
        Получение команды по её идентификатору.

        :returns False Команда не найдена
        """
        team = await self.team_repository.get_team_by_id(team_id)

        if not team:
            return None, False

        return team, True

    async def add_hacker_to_team(self, team_id: UUID, hacker_id: UUID) -> Tuple[Optional[Team], int]:
        """
        Добавление участника в команду.

        :returns -1 Команда не найдена
        :returns -2 Хакер не найден
        :returns -3 Команда уже заполнена
        :returns -4 Хакер уже в команде
        :returns -5 Ошибка при добавлении хакера
        """
        # Получаем хакера по ID
        hacker = await self.hacker_repository.get_hacker_by_id(hacker_id)
        if not hacker:
            logger.error(f"Хакер с id={hacker_id} не найден")
            return None, -2

        # Добавляем хакера в команду
        team, status_code = await self.team_repository.add_hacker_to_team(team_id, hacker)
        
        if status_code < 0:
            if status_code == -1:
                logger.error(f"Команда с id={team_id} не найдена")
            elif status_code == -3:
                logger.error(f"Команда с id={team_id} уже заполнена")
            elif status_code == -4:
                logger.warning(f"Хакер {hacker_id} уже в команде {team_id}")
            elif status_code == -5:
                logger.error(f"Ошибка при добавлении хакера {hacker_id} в команду {team_id}")
        
        return team, status_code

    async def get_teams_by_hackathon_id(self, hackathon_id: UUID) -> List[Team]:
        """
        Получение всех команд, связанных с указанным хакатоном.
        """
        teams = await self.team_repository.get_teams_by_hackathon_id(hackathon_id)
        
        if not teams:
            logger.info(f"Команды не найдены для хакатона с id={hackathon_id}")
            
        return teams

    async def get_teams_by_user_id(self, user_id: UUID) -> List[Team]:
        """
        Получение всех команд пользователя.
        
        Находит команды, в которых участвует пользователь с указанным user_id.
        """
        teams = await self.team_repository.get_teams_by_user_id(user_id)
        
        if not teams:
            logger.info(f"Команды не найдены для пользователя с user_id={user_id}")
            
        return teams

