from sqlalchemy.orm import relationship

from persistent.db.base import Base, WithMetadata
from sqlalchemy import Column, Text, Integer, Boolean, DateTime, Float, UUID, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime


# Таблица для хакатона
class Hackathon(Base, WithMetadata):
    __tablename__ = "hackathon"

    name = Column(Text, nullable=False)
    task_description = Column(Text, nullable=True)
    start_of_registration = Column(DateTime, nullable=True)
    end_of_registration = Column(DateTime, nullable=True)
    start_of_hack = Column(DateTime, nullable=False)
    end_of_hack = Column(DateTime, nullable=True)
    amount_money = Column(Float, nullable=True)
    type = Column(Text, nullable=True)  # \"online\" или \"offline\"
    url = Column(Text, nullable=True)  # URL страницы хакатона
    winner_solutions = relationship("WinnerSolution", back_populates="hackathon", lazy='subquery')
    teams = relationship("Team", back_populates="hackathon", lazy='subquery')

    __table_args__ = (UniqueConstraint("name", "start_of_hack", name="uq_name_start_of_hack"),)
