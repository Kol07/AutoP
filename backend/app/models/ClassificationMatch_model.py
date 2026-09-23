from sqlalchemy import Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from .enums import RELEVANCE_RESULT_ENUM, RelevanceResult
from .mixins import CreatedAtMixin, IdMixin


class ClassificationMatch(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "classification_matches"
    __table_args__ = (
        UniqueConstraint(
            "classification_run_id",
            "matched_article_id",
            name="uq_classification_matches_run_article",
        ),
    )

    classification_run_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("classification_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    matched_article_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("articles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    matched_decision: Mapped[RelevanceResult] = mapped_column(
        RELEVANCE_RESULT_ENUM,
        nullable=False,
    )
