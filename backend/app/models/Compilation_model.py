from datetime import date

from sqlalchemy import Date, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from .mixins import IdMixin, SoftDeleteMixin, TimestampMixin


class Compilation(IdMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "compilations"

    name: Mapped[str] = mapped_column(Text, nullable=False)
    compilation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
