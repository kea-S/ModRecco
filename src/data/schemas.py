from enum import Enum
from datetime import date, datetime
from typing import List, Dict, Any, Union, Optional
import uuid
from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy import func
from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB


class Base(DeclarativeBase):
    pass


PrereqTree = Union[str, Dict[str, Any]]


class WeekRange:
    start: date
    end: date
    weekInterval: int
    weeks: List[int]


class Lesson:
    classNo: str
    startTime: str
    endTime: str
    weeks: Union[WeekRange, List[int]]
    venue: str
    day: str
    lessonType: str
    size: int


class SemesterData:
    semester: int
    examDate: datetime
    examDuration: int
    timetable: Lesson


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    vector_embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(64))   # size for now

    interactions: Mapped[List["UserInteraction"]] = relationship(back_populates="user", passive_deletes=True)


class Module(Base):
    __tablename__ = "modules"

    module_code: Mapped[str] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()
    department: Mapped[str] = mapped_column()
    faculty: Mapped[str] = mapped_column()
    module_credit: Mapped[int] = mapped_column()
    vector_embedding: Mapped[List[float]] = mapped_column(Vector(64),
                                                          nullable=True)   # size for now
    semester_data: Mapped[SemesterData] = mapped_column(JSONB)
    prereq_tree: Mapped[Optional[PrereqTree]] = mapped_column(JSONB)


class ActionType(str, Enum):
    CLICK = "Click"
    SAVE = "Save"
    ADD = "Add"


class UserInteraction(Base):
    __tablename__ = "user_interactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    action: Mapped[ActionType] = mapped_column(SQLEnum(ActionType))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                server_default=func.now(),
                                                index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id",
                                                          ondelete="CASCADE"),
                                               index=True
                                               )
    module_code: Mapped[str] = mapped_column(ForeignKey("modules.module_code",
                                                        ondelete="CASCADE"),
                                             index=True)

    user: Mapped["User"] = relationship(back_populates="interactions")
    module: Mapped["Module"] = relationship()
