"""Create the initial POROTW schema.

Revision ID: 20260917_0001
Revises:
Create Date: 2026-09-17
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


revision: str = "20260917_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


processing_status = postgresql.ENUM(
    "processing",
    "pending_review",
    "reviewed",
    "failed",
    name="processing_status",
    create_type=False,
)
relevance_result = postgresql.ENUM(
    "relevant",
    "irrelevant",
    name="relevance_result",
    create_type=False,
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE processing_status AS ENUM (
                'processing', 'pending_review', 'reviewed', 'failed'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE relevance_result AS ENUM ('relevant', 'irrelevant');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$
        """
    )

    op.create_table(
        "processing_batches",
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("status", processing_status, nullable=False),
        sa.Column("total_articles", sa.Integer(), nullable=False),
        sa.Column("processed_articles", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_processing_batches")),
    )
    op.create_table(
        "compilations",
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("compilation_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_compilations")),
    )
    op.create_table(
        "articles",
        sa.Column("processing_batch_id", sa.String(length=26), nullable=False),
        sa.Column("compilation_id", sa.String(length=26), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["compilation_id"],
            ["compilations.id"],
            name=op.f("fk_articles_compilation_id_compilations"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["processing_batch_id"],
            ["processing_batches.id"],
            name=op.f("fk_articles_processing_batch_id_processing_batches"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_articles")),
        sa.UniqueConstraint("content_hash", name=op.f("uq_articles_content_hash")),
    )
    op.create_index(
        op.f("ix_articles_compilation_id"),
        "articles",
        ["compilation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_articles_processing_batch_id"),
        "articles",
        ["processing_batch_id"],
        unique=False,
    )
    op.create_table(
        "article_embeddings",
        sa.Column("article_id", sa.String(length=26), nullable=False),
        sa.Column("model_name", sa.Text(), nullable=False),
        sa.Column("model_revision", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(), nullable=False),
        sa.Column("embedding_dimension", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["article_id"],
            ["articles.id"],
            name=op.f("fk_article_embeddings_article_id_articles"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_article_embeddings")),
        sa.UniqueConstraint(
            "article_id",
            "model_name",
            "model_revision",
            name="uq_article_embeddings_article_model_revision",
        ),
    )

    op.create_table(
        "classification_runs",
        sa.Column("article_id", sa.String(length=26), nullable=False),
        sa.Column("guideline_result", relevance_result, nullable=False),
        sa.Column("guideline_reason", sa.Text(), nullable=True),
        sa.Column("guideline_hits", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("motherhood_result", relevance_result, nullable=False),
        sa.Column("motherhood_reason", sa.Text(), nullable=True),
        sa.Column("system_prediction", relevance_result, nullable=True),
        sa.Column("llm_model", sa.Text(), nullable=False),
        sa.Column("embedding_model", sa.Text(), nullable=False),
        sa.Column("status", processing_status, nullable=False),
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["article_id"],
            ["articles.id"],
            name=op.f("fk_classification_runs_article_id_articles"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_classification_runs")),
    )
    op.create_index(
        op.f("ix_classification_runs_article_id"),
        "classification_runs",
        ["article_id"],
        unique=False,
    )
    op.create_table(
        "reviews",
        sa.Column("classification_run_id", sa.String(length=26), nullable=False),
        sa.Column("decision", relevance_result, nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.Text(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["classification_run_id"],
            ["classification_runs.id"],
            name=op.f("fk_reviews_classification_run_id_classification_runs"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reviews")),
        sa.UniqueConstraint(
            "classification_run_id",
            name=op.f("uq_reviews_classification_run_id"),
        ),
    )
    op.create_table(
        "classification_matches",
        sa.Column("classification_run_id", sa.String(length=26), nullable=False),
        sa.Column("matched_article_id", sa.String(length=26), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("matched_decision", relevance_result, nullable=False),
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["classification_run_id"],
            ["classification_runs.id"],
            name=op.f(
                "fk_classification_matches_classification_run_id_classification_runs"
            ),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["matched_article_id"],
            ["articles.id"],
            name=op.f("fk_classification_matches_matched_article_id_articles"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_classification_matches")),
        sa.UniqueConstraint(
            "classification_run_id",
            "matched_article_id",
            name="uq_classification_matches_run_article",
        ),
        sa.UniqueConstraint(
            "classification_run_id",
            "rank",
            name="uq_classification_matches_run_rank",
        ),
    )

    op.create_index(
        op.f("ix_classification_matches_matched_article_id"),
        "classification_matches",
        ["matched_article_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("classification_matches")
    op.drop_table("reviews")
    op.drop_table("classification_runs")
    op.drop_table("article_embeddings")
    op.drop_table("articles")
    op.drop_table("compilations")
    op.drop_table("processing_batches")
    op.execute("DROP TYPE IF EXISTS relevance_result")
    op.execute("DROP TYPE IF EXISTS processing_status")
