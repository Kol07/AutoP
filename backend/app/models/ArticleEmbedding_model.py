from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from .mixins import CreatedAtMixin, IdMixin


class ArticleEmbedding(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "article_embeddings"
    __table_args__ = (
        UniqueConstraint(
            "article_id",
            "model_name",
            "model_revision",
            name="uq_article_embeddings_article_model_revision",
        ),
    )

    article_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("articles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(Text, nullable=False)
    model_revision: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(), nullable=False)
    embedding_dimension: Mapped[int] = mapped_column(Integer, nullable=False)
