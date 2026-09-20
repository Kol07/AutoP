from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from .mixins import IdMixin, SoftDeleteMixin, TimestampMixin


class Article(IdMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "articles"

    processing_batch_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("processing_batches.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    compilation_id: Mapped[str | None] = mapped_column(
        String(26),
        ForeignKey("compilations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    content_hash: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
