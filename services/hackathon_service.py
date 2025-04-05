from datetime import datetime
from typing import List, Optional, Tuple
from loguru import logger
from sqlalchemy import UUID

from persistent.db.hackathon import Hackathon
from persistent.db.winner_solution import WinnerSolution
from repository.hackathon_repository import HackathonRepository


class HackathonService:
    def __init__(self) -> None:
        self.hackathon_repository = HackathonRepository()

    async def get_all_hackathons(self) -> List[Hackathon]:
        """
        Возвращает все хакатоны.
        """
        hackathons = await self.hackathon_repository.get_all_hackathons()

        return hackathons

    async def upsert_hackathon(
        self,
        name: str,
        task_description: str,
        start_of_registration: datetime,
        end_of_registration: datetime,
        start_of_hack: datetime,
        end_of_hack: datetime,
        amount_money: float,
        type: str,
        url: str = None,
    ) -> UUID:
        """
        Создаёт или обновляет хакатон.
        """
        hackathon_id = await self.hackathon_repository.upsert_hackathon(
            name, task_description, start_of_registration,
            end_of_registration, start_of_hack, end_of_hack,
            amount_money, type, url
        )

        return hackathon_id

    async def get_hackathon_by_id(self, hackathon_id: UUID) -> Optional[Hackathon]:
        """
        Возвращает хакатон по ID.

        :returns None если хакатон не найден
        """
        hackathon = await self.hackathon_repository.get_hackathon_by_id(hackathon_id)
        return hackathon
