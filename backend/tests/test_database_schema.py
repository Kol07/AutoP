import io
import sys
import unittest
import warnings
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Enum, inspect
from sqlalchemy.exc import SAWarning
from sqlalchemy.orm import configure_mappers
from sqlalchemy.schema import UniqueConstraint


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.base import Base  # noqa: E402
from app.models import (  # noqa: E402
    Article,
    ArticleEmbedding,
    ClassificationMatch,
    ClassificationRun,
    Compilation,
    ProcessingBatch,
    Review,
)
from app.models.mixins import generate_ulid  # noqa: E402


class ModelSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("error", SAWarning)
            configure_mappers()

    def test_expected_tables_are_registered(self) -> None:
        self.assertEqual(
            set(Base.metadata.tables),
            {
                "processing_batches",
                "compilations",
                "articles",
                "article_embeddings",
                "classification_runs",
                "reviews",
                "classification_matches",
            },
        )

    def test_generated_ulids_are_unique_26_character_values(self) -> None:
        first = generate_ulid()
        second = generate_ulid()

        self.assertEqual(len(first), 26)
        self.assertEqual(len(second), 26)
        self.assertNotEqual(first, second)

    def test_relationships_are_bidirectional_and_have_expected_shape(self) -> None:
        expectations = {
            ProcessingBatch: {"articles": (True, "processing_batch")},
            Compilation: {"articles": (True, "compilation")},
            Article: {
                "processing_batch": (False, "articles"),
                "compilation": (False, "articles"),
                "embeddings": (True, "article"),
                "classification_runs": (True, "article"),
                "classification_matches": (True, "matched_article"),
            },
            ArticleEmbedding: {"article": (False, "embeddings")},
            ClassificationRun: {
                "article": (False, "classification_runs"),
                "review": (False, "classification_run"),
                "matches": (True, "classification_run"),
            },
            Review: {"classification_run": (False, "review")},
            ClassificationMatch: {
                "classification_run": (False, "matches"),
                "matched_article": (False, "classification_matches"),
            },
        }

        for model, relationships in expectations.items():
            mapper_relationships = inspect(model).relationships
            self.assertEqual(set(mapper_relationships.keys()), set(relationships))
            for name, (uselist, back_populates) in relationships.items():
                relationship = mapper_relationships[name]
                self.assertEqual(relationship.uselist, uselist)
                self.assertEqual(relationship.back_populates, back_populates)

    def test_foreign_key_delete_policies_and_indexes(self) -> None:
        expected = {
            ("articles", "processing_batch_id"): "RESTRICT",
            ("articles", "compilation_id"): "SET NULL",
            ("article_embeddings", "article_id"): "RESTRICT",
            ("classification_runs", "article_id"): "RESTRICT",
            ("reviews", "classification_run_id"): "RESTRICT",
            ("classification_matches", "classification_run_id"): "RESTRICT",
            ("classification_matches", "matched_article_id"): "RESTRICT",
        }

        for (table_name, column_name), ondelete in expected.items():
            column = Base.metadata.tables[table_name].c[column_name]
            foreign_key = next(iter(column.foreign_keys))
            self.assertEqual(foreign_key.ondelete, ondelete)
            if not column.unique:
                self.assertTrue(column.index)

    def test_unique_constraints_match_the_erd(self) -> None:
        expected = {
            "articles": {("content_hash",)},
            "article_embeddings": {
                ("article_id", "model_name", "model_revision"),
            },
            "reviews": {("classification_run_id",)},
            "classification_matches": {
                ("classification_run_id", "matched_article_id"),
                ("classification_run_id", "rank"),
            },
        }

        for table_name, expected_columns in expected.items():
            table = Base.metadata.tables[table_name]
            actual_columns = {
                tuple(constraint.columns.keys())
                for constraint in table.constraints
                if isinstance(constraint, UniqueConstraint)
            }
            self.assertEqual(actual_columns, expected_columns)

    def test_native_enums_store_erd_values(self) -> None:
        status_type = ProcessingBatch.__table__.c.status.type
        result_type = ClassificationRun.__table__.c.guideline_result.type

        self.assertIsInstance(status_type, Enum)
        self.assertTrue(status_type.native_enum)
        self.assertEqual(status_type.name, "processing_status")
        self.assertEqual(
            status_type.enums,
            ["processing", "pending_review", "reviewed", "failed"],
        )
        self.assertIsInstance(result_type, Enum)
        self.assertTrue(result_type.native_enum)
        self.assertEqual(result_type.name, "relevance_result")
        self.assertEqual(result_type.enums, ["relevant", "irrelevant"])


class OfflineMigrationTests(unittest.TestCase):
    def _config(self) -> Config:
        config = Config(str(BACKEND_ROOT / "alembic.ini"))
        config.output_buffer = io.StringIO()
        return config

    def test_upgrade_compiles_without_a_database_connection(self) -> None:
        config = self._config()
        command.upgrade(config, "head", sql=True)
        sql = config.output_buffer.getvalue()

        self.assertIn("CREATE EXTENSION IF NOT EXISTS vector", sql)
        self.assertIn("CREATE TABLE processing_batches", sql)
        self.assertIn("CREATE TABLE classification_matches", sql)
        self.assertIn("CREATE INDEX ix_articles_processing_batch_id", sql)

    def test_downgrade_compiles_without_a_database_connection(self) -> None:
        config = self._config()
        command.downgrade(config, "20260917_0001:base", sql=True)
        sql = config.output_buffer.getvalue()

        self.assertIn("DROP TABLE processing_batches", sql)
        self.assertIn("DROP TYPE IF EXISTS relevance_result", sql)
        self.assertNotIn("DROP EXTENSION", sql)


if __name__ == "__main__":
    unittest.main()
