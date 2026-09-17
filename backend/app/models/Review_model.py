from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from .enums import RELEVANCE_RESULT_ENUM, RelevanceResult
from .mixins import IdMixin, TimestampMixin


class Review(IdMixin, TimestampMixin, Base):
    __tablename__ = "reviews"

    classification_run_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("classification_runs.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    decision: Mapped[RelevanceResult] = mapped_column(
        RELEVANCE_RESULT_ENUM,
        nullable=False,
    )
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[str] = mapped_column(Text, nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
