from typing import Any

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from .enums import (
    PROCESSING_STATUS_ENUM,
    RELEVANCE_RESULT_ENUM,
    ProcessingStatus,
    RelevanceResult,
)
from .mixins import IdMixin, TimestampMixin


class ClassificationRun(IdMixin, TimestampMixin, Base):
    __tablename__ = "classification_runs"

    article_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("articles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    guideline_result: Mapped[RelevanceResult] = mapped_column(
        RELEVANCE_RESULT_ENUM,
        nullable=False,
    )
    guideline_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    guideline_hits: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    motherhood_result: Mapped[RelevanceResult] = mapped_column(
        RELEVANCE_RESULT_ENUM,
        nullable=False,
    )
    motherhood_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_prediction: Mapped[RelevanceResult | None] = mapped_column(
        RELEVANCE_RESULT_ENUM,
        nullable=True,
    )
    llm_model: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_model: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ProcessingStatus] = mapped_column(
        PROCESSING_STATUS_ENUM,
        nullable=False,
    )
