from enum import Enum
from datetime import date, datetime
from typing import List, Union, Optional, TypeAlias, Tuple
import uuid
from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy import func
from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel, Field


class Base(DeclarativeBase):
    pass


class PrereqNode(BaseModel):
    # 'and' and 'or' are reserved keywords in Python, so we use aliases
    and_list: Optional[List["PrereqTree"]] = Field(None, alias="and")
    or_list: Optional[List["PrereqTree"]] = Field(None, alias="or")

    # nOf is [int, List[PrereqTree]], e.g., [2, ["CS1010", "CS2100"]]
    n_of: Optional[Tuple[int, List["PrereqTree"]]] = Field(None, alias="nOf")


# PrereqTree is either a string or one of the node types
PrereqTree: TypeAlias = Union[str, PrereqNode]

# Rebuild to allow the recursive string reference "PrereqTree"
PrereqNode.model_rebuild()


class WeekRange(BaseModel):
    start: date
    end: date
    weekInterval: Optional[int] = None
    weeks: Optional[List[int]] = None


class Lesson(BaseModel):
    classNo: str
    startTime: str
    endTime: str
    weeks: Union[WeekRange, List[int]]
    venue: str
    day: str
    lessonType: str
    size: int
    covidZone: str


class SemesterData(BaseModel):
    semester: int
    examDate: Optional[datetime] = None
    examDuration: Optional[int] = None
    timetable: List[Lesson]
    covidZones: List[str]


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
    semester_data: Mapped[List[SemesterData]] = mapped_column(JSONB)
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
