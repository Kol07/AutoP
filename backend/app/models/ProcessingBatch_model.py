from datetime import datetime

from sqlalchemy import DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from .enums import PROCESSING_STATUS_ENUM, ProcessingStatus
from .mixins import CreatedAtMixin, IdMixin


class ProcessingBatch(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "processing_batches"

    filename: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ProcessingStatus] = mapped_column(
        PROCESSING_STATUS_ENUM,
        nullable=False,
    )
    total_articles: Mapped[int] = mapped_column(Integer, nullable=False)
    processed_articles: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
