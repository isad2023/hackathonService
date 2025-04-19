from datetime import datetime
from typing import List, Optional, cast
from loguru import logger
from sqlalchemy import select, delete, UUID
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from infrastructure.db.connection import pg_connection
from persistent.db.hackathon import Hackathon


class HackathonRepository:
    def __init__(self) -> None:
        self._sessionmaker = pg_connection()

    async def get_all_hackathons(self) -> List[Hackathon]:
        """
        Получение всех хакатонов.
        """
        stmt = select(Hackathon)

        async with self._sessionmaker() as session:
            resp = await session.execute(stmt)

            rows = resp.fetchall()  # Извлекаем все строки
            hackathons = [row[0] for row in rows]  # Преобразуем их в список объектов Hacker
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
            city: Optional[str],
            approved: bool,
            url: str = None,
    ) -> Optional[UUID]:
        """
        Создание нового хакатона.
        """
        stmt = insert(Hackathon).values({
            "name": name,
            "task_description": task_description,
            "start_of_registration": start_of_registration,
            "end_of_registration": end_of_registration,
            "start_of_hack": start_of_hack,
            "end_of_hack": end_of_hack,
            "amount_money": amount_money,
            "type": type,
            "city": city,
            "approved": approved,
            "url": url,
        })

        stmt.on_conflict_do_update(constraint="uq_name_start_of_hack", set_={
            "task_description": task_description,
            "start_of_registration": start_of_registration,
            "end_of_registration": end_of_registration,
            "end_of_hack": end_of_hack,
            "amount_money": amount_money,
            "type": type,
            "city": city,
            "approved": approved,
            "url": url,
            "updated_at": datetime.utcnow(),
        })

        async with self._sessionmaker() as session:
            result = await session.execute(stmt)
            hackathon_id = result.inserted_primary_key[0]

            await session.commit()

        return hackathon_id

    async def get_hackathon_by_id(self, hackathon_id: UUID) -> Optional[Hackathon]:
        """
        Получение хакатона по ID.
        """
        stmt = select(Hackathon).where(cast("ColumnElement[bool]", Hackathon.id == hackathon_id)).limit(1)

        async with self._sessionmaker() as session:
            resp = await session.execute(stmt)

        row = resp.fetchone()
        return row[0] if row else None
