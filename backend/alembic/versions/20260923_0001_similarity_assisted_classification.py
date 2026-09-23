"""Add similarity-assisted classification results and remove match rank.

Revision ID: 20260923_0001
Revises: 62e573ed0016
Create Date: 2026-09-23
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260923_0001"
down_revision: str | None = "62e573ed0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


relevance_result = postgresql.ENUM(
    "relevant",
    "irrelevant",
    name="relevance_result",
    create_type=False,
)


def upgrade() -> None:
    op.add_column(
        "classification_runs",
        sa.Column("similarity_result", relevance_result, nullable=True),
    )
    op.add_column(
        "classification_runs",
        sa.Column("confidence_score", sa.Float(), nullable=True),
    )
    op.create_check_constraint(
        op.f("ck_classification_runs_confidence_score_range"),
        "classification_runs",
        "confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)",
    )

    op.drop_constraint(
        "uq_classification_matches_run_rank",
        "classification_matches",
        type_="unique",
    )
    op.drop_column("classification_matches", "rank")


def downgrade() -> None:
    op.add_column(
        "classification_matches",
        sa.Column("rank", sa.Integer(), nullable=True),
    )
    op.execute(
        """
        WITH ranked_matches AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY classification_run_id
                    ORDER BY similarity_score DESC, matched_article_id ASC
                ) AS reconstructed_rank
            FROM classification_matches
        )
        UPDATE classification_matches AS classification_match
        SET rank = ranked_matches.reconstructed_rank
        FROM ranked_matches
        WHERE classification_match.id = ranked_matches.id
        """
    )
    op.alter_column(
        "classification_matches",
        "rank",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.create_unique_constraint(
        "uq_classification_matches_run_rank",
        "classification_matches",
        ["classification_run_id", "rank"],
    )

    op.drop_constraint(
        op.f("ck_classification_runs_confidence_score_range"),
        "classification_runs",
        type_="check",
    )
    op.drop_column("classification_runs", "confidence_score")
    op.drop_column("classification_runs", "similarity_result")
