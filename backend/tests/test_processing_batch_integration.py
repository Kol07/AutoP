import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient
from pydantic import ValidationError


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.models.enums import ProcessingStatus  # noqa: E402
from app.dependencies import (  # noqa: E402
    get_pipeline_service,
    get_processing_batch_service,
)
from app.main import app  # noqa: E402
from app.schemas.article_schema import ArticleIngest  # noqa: E402
from app.schemas.processingBatch_schema import (  # noqa: E402
    ProcessingBatchDetail,
    ProcessingBatchIngest,
    ProcessingBatchSummary,
)
from app.services.pipeline_service import PipelineService  # noqa: E402


class FakeDatabase:
    def __init__(self) -> None:
        self.committed = False
        self.rolledBack = False

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolledBack = True

    async def refresh(self, value) -> None:
        return None


class FakeBatchService:
    def __init__(self) -> None:
        self.db = FakeDatabase()

    async def create_batch(self, data, *, commit=True):
        return SimpleNamespace(
            id="batch-id",
            filename=data.filename,
            status=ProcessingStatus.PROCESSING,
            total_articles=0,
            processed_articles=0,
            created_at=datetime.now(timezone.utc),
            completed_at=None,
        )


class FakeArticleService:
    def __init__(self, accepted: list[bool]) -> None:
        self.accepted = iter(accepted)

    async def create_article(self, data, *, commit=True):
        return SimpleNamespace(id="article") if next(self.accepted) else None


def make_pipeline(batchService, articleService) -> PipelineService:
    return PipelineService(
        batchService=batchService,
        articleService=articleService,
        articleEmbeddingService=SimpleNamespace(),
        classificationService=SimpleNamespace(),
        sessionFactory=SimpleNamespace(),
    )


class ProcessingBatchContractTests(unittest.TestCase):
    def test_ingest_request_rejects_an_empty_article_list(self) -> None:
        with self.assertRaises(ValidationError):
            ProcessingBatchIngest(fileName="empty.json", articles=[])

    def test_summary_serializes_with_camel_case_fields(self) -> None:
        payload = ProcessingBatchSummary(
            id="batch-id",
            fileName="articles.json",
            status=ProcessingStatus.PROCESSING,
            totalArticles=2,
            processedArticles=0,
            createdAt=datetime.now(timezone.utc),
        ).model_dump(mode="json")

        self.assertIn("fileName", payload)
        self.assertIn("totalArticles", payload)
        self.assertNotIn("filename", payload)


class ProcessingBatchPreparationTests(unittest.IsolatedAsyncioTestCase):
    async def test_only_accepted_articles_count_toward_the_batch(self) -> None:
        batchService = FakeBatchService()
        pipeline = make_pipeline(
            batchService,
            FakeArticleService([True, False]),
        )

        batch = await pipeline.create_ingest_batch(
            "articles.json",
            [
                ArticleIngest(recordTitle="One", recordContent="First"),
                ArticleIngest(recordTitle="Two", recordContent="Duplicate"),
            ],
        )

        self.assertEqual(batch.total_articles, 1)
        self.assertEqual(batch.status, ProcessingStatus.PROCESSING)
        self.assertTrue(batchService.db.committed)

    async def test_zero_accepted_articles_complete_without_background_work(self) -> None:
        batchService = FakeBatchService()
        pipeline = make_pipeline(batchService, FakeArticleService([False]))

        batch = await pipeline.create_ingest_batch(
            "duplicates.json",
            [ArticleIngest(recordTitle="Duplicate", recordContent="Same")],
        )

        self.assertEqual(batch.total_articles, 0)
        self.assertEqual(batch.status, ProcessingStatus.PENDING_REVIEW)
        self.assertIsNotNone(batch.completed_at)


class ProcessingBatchBackgroundTests(unittest.IsolatedAsyncioTestCase):
    async def test_workflow_failure_marks_the_batch_failed(self) -> None:
        statuses = []

        class FailingEmbeddingService:
            async def process_batch(self, batchID):
                raise RuntimeError("embedding failed")

        pipeline = PipelineService(
            batchService=SimpleNamespace(),
            articleService=SimpleNamespace(),
            articleEmbeddingService=FailingEmbeddingService(),
            classificationService=SimpleNamespace(),
            sessionFactory=SimpleNamespace(),
        )

        async def finish_batch(batchID, status):
            statuses.append(status)

        pipeline._finish_batch = finish_batch

        await pipeline.run_workflows("batch-id")

        self.assertEqual(statuses, [ProcessingStatus.FAILED])


class ProcessingBatchRouteTests(unittest.TestCase):
    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_latest_returns_404_when_no_batch_exists(self) -> None:
        class EmptyBatchService:
            async def fetch_latest_detail(self):
                return None

        app.dependency_overrides[get_processing_batch_service] = EmptyBatchService

        with TestClient(app) as client:
            response = client.get("/api/v1/processing-batches/latest")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "No processing batch found")

    def test_batch_detail_uses_the_camel_case_response_contract(self) -> None:
        detail = ProcessingBatchDetail(
            id="batch-id",
            fileName="articles.json",
            status=ProcessingStatus.PENDING_REVIEW,
            totalArticles=0,
            processedArticles=0,
            createdAt=datetime.now(timezone.utc),
            completedAt=datetime.now(timezone.utc),
            articles=[],
        )

        class DetailBatchService:
            async def fetch_detail(self, batchID):
                return detail if batchID == "batch-id" else None

        app.dependency_overrides[get_processing_batch_service] = DetailBatchService

        with TestClient(app) as client:
            response = client.get("/api/v1/processing-batches/batch-id")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["fileName"], "articles.json")
        self.assertEqual(response.json()["totalArticles"], 0)

    def test_post_returns_202_and_schedules_processing(self) -> None:
        processed = []
        now = datetime.now(timezone.utc)

        class FakePipeline:
            async def create_ingest_batch(self, fileName, articlesList):
                return SimpleNamespace(
                    id="batch-id",
                    filename=fileName,
                    status=ProcessingStatus.PROCESSING,
                    total_articles=len(articlesList),
                    processed_articles=0,
                    created_at=now,
                    completed_at=None,
                )

            async def run_workflows(self, batchID):
                processed.append(batchID)

        app.dependency_overrides[get_pipeline_service] = FakePipeline

        with TestClient(app) as client:
            response = client.post(
                "/api/v1/processing-batches",
                json={
                    "fileName": "articles.json",
                    "articles": [
                        {
                            "recordTitle": "Title",
                            "recordContent": "Content",
                        }
                    ],
                },
            )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["id"], "batch-id")
        self.assertEqual(processed, ["batch-id"])


if __name__ == "__main__":
    unittest.main()
