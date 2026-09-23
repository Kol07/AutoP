import asyncio
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy.dialects import postgresql


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.models.enums import ProcessingStatus, RelevanceResult  # noqa: E402
from app.models.ArticleEmbedding_model import ArticleEmbedding  # noqa: E402
from app.repositories.articleEmbedding_repository import (  # noqa: E402
    ArticleEmbeddingRepository,
)
from app.schemas.classification_schema import (  # noqa: E402
    GuidelineHit,
    LLMClassificationResult,
)
from app.schemas.similarity_schema import (  # noqa: E402
    SimilarArticleMatch,
    SimilarityClassificationResult,
)
from app.services.articleSimilarity_service import (  # noqa: E402
    ArticleSimilarityService,
)
from app.services.classificationService import ClassificationService  # noqa: E402
from app.services.classification_config import ClassificationSettings  # noqa: E402
from app.services.pipeline_service import PipelineService  # noqa: E402


class FakeSession:
    def __init__(self) -> None:
        self.committed = False
        self.rolledBack = False
        self.refreshed = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolledBack = True

    async def refresh(self, value) -> None:
        self.refreshed = value


class FakeSessionFactory:
    def __init__(self, session: FakeSession | None = None) -> None:
        self.session = session or FakeSession()

    def __call__(self):
        return self.session


class ClassificationScoringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = ClassificationSettings()
        self.service = ClassificationService(
            sessionFactory=FakeSessionFactory(),
            llmService=SimpleNamespace(),
            similarityService=SimpleNamespace(),
            settings=self.settings,
        )

    def test_no_similarity_reweights_available_signals(self) -> None:
        llmResult = LLMClassificationResult(
            guidelineResult=RelevanceResult.RELEVANT,
            guidelineHits=[GuidelineHit(guidelineID="g1", reason="hit")],
            motherhoodResult=RelevanceResult.RELEVANT,
        )

        score = self.service._calculate_confidence(
            llmResult,
            SimilarityClassificationResult(),
        )

        self.assertAlmostEqual(score, (0.60 / 3 + 0.10) / 0.70)
        self.assertEqual(
            self.service._get_system_prediction(0.50),
            RelevanceResult.RELEVANT,
        )

    def test_guideline_hits_are_capped(self) -> None:
        llmResult = LLMClassificationResult(
            guidelineResult=RelevanceResult.RELEVANT,
            guidelineHits=[
                GuidelineHit(guidelineID=f"g{index}", reason="hit")
                for index in range(5)
            ],
            motherhoodResult=RelevanceResult.IRRELEVANT,
        )
        similarityResult = SimilarityClassificationResult(
            result=RelevanceResult.IRRELEVANT,
            score=0,
        )

        score = self.service._calculate_confidence(llmResult, similarityResult)

        self.assertAlmostEqual(score, 0.60)


class SimilarityResultTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ArticleSimilarityService(
            sessionFactory=FakeSessionFactory(),
            settings=ClassificationSettings(),
        )

    def test_similarity_weighted_tie_is_relevant(self) -> None:
        result = self.service._calculate_result(
            [
                SimilarArticleMatch(
                    articleID="relevant",
                    similarityScore=0.9,
                    relevanceResult=RelevanceResult.RELEVANT,
                ),
                SimilarArticleMatch(
                    articleID="irrelevant",
                    similarityScore=0.9,
                    relevanceResult=RelevanceResult.IRRELEVANT,
                ),
            ]
        )

        self.assertEqual(result.score, 0.5)
        self.assertEqual(result.result, RelevanceResult.RELEVANT)

    def test_no_matches_have_no_score_or_verdict(self) -> None:
        result = self.service._calculate_result([])

        self.assertIsNone(result.score)
        self.assertIsNone(result.result)
        self.assertEqual(result.matches, [])


class SimilarityQueryTests(unittest.IsolatedAsyncioTestCase):
    async def test_query_filters_and_orders_historical_reviewed_articles(self) -> None:
        class EmptyResult:
            def all(self):
                return []

        class CapturingDatabase:
            def __init__(self):
                self.statement = None

            async def execute(self, statement):
                self.statement = statement
                return EmptyResult()

        database = CapturingDatabase()
        targetEmbedding = ArticleEmbedding(
            article_id="current-article",
            model_name="embedding-model",
            model_revision="revision-1",
            embedding=[1.0, 0.0],
            embedding_dimension=2,
        )

        await ArticleEmbeddingRepository(database).find_reviewed_similar(
            targetEmbedding=targetEmbedding,
            excludedBatchID="current-batch",
            minimumScore=0.70,
            limit=5,
        )

        compiled = database.statement.compile(dialect=postgresql.dialect())
        sql = str(compiled)

        self.assertIn("PARTITION BY classification_runs.article_id", sql)
        self.assertIn("ORDER BY reviews.reviewed_at DESC, reviews.id DESC", sql)
        self.assertIn("articles.processing_batch_id !=", sql)
        self.assertIn("articles.deleted_at IS NULL", sql)
        self.assertIn("article_embeddings.model_name =", sql)
        self.assertIn("article_embeddings.model_revision =", sql)
        self.assertIn("article_embeddings.embedding_dimension =", sql)
        self.assertIn("anon_1.review_number =", sql)
        self.assertIn("article_embeddings.embedding <=>", sql)
        self.assertIn("article_embeddings.article_id ASC", sql)
        self.assertIn(0.70, compiled.params.values())
        self.assertIn(5, compiled.params.values())


class ClassificationOrchestrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_llm_and_similarity_run_concurrently_and_persist_atomically(self) -> None:
        started = set()
        bothStarted = asyncio.Event()
        release = asyncio.Event()

        async def wait_for_peer(name: str):
            started.add(name)
            if len(started) == 2:
                bothStarted.set()
            await release.wait()

        class FakeLLMService:
            async def classify_article(self, content: str):
                await wait_for_peer("llm")
                return LLMClassificationResult(
                    guidelineResult=RelevanceResult.RELEVANT,
                    guidelineHits=[
                        GuidelineHit(guidelineID=f"g{index}", reason="hit")
                        for index in range(3)
                    ],
                    motherhoodResult=RelevanceResult.IRRELEVANT,
                )

        match = SimilarArticleMatch(
            articleID="historical-article",
            similarityScore=0.9,
            relevanceResult=RelevanceResult.RELEVANT,
        )

        class FakeSimilarityService:
            async def classify_article(self, articleID: str):
                await wait_for_peer("similarity")
                return SimilarityClassificationResult(
                    result=RelevanceResult.RELEVANT,
                    score=1,
                    matches=[match],
                )

        class RecordingRepository:
            instance = None

            def __init__(self, db):
                self.data = None
                self.matches = None
                RecordingRepository.instance = self

            async def create(self, data):
                self.data = data
                return SimpleNamespace(id="classification-run")

            async def create_matches(self, classificationRunID, matches):
                self.matches = (classificationRunID, matches)

        session = FakeSession()
        service = ClassificationService(
            sessionFactory=FakeSessionFactory(session),
            llmService=FakeLLMService(),
            similarityService=FakeSimilarityService(),
            settings=ClassificationSettings(),
        )

        with patch(
            "app.services.classificationService.ClassificationRunRepository",
            RecordingRepository,
        ):
            task = asyncio.create_task(
                service.process_article("current-article", "article content")
            )
            await asyncio.wait_for(bothStarted.wait(), timeout=1)
            self.assertEqual(started, {"llm", "similarity"})
            release.set()
            await task

        repository = RecordingRepository.instance
        self.assertTrue(session.committed)
        self.assertFalse(session.rolledBack)
        self.assertEqual(repository.data.status, ProcessingStatus.PENDING_REVIEW)
        self.assertAlmostEqual(repository.data.confidenceScore, 0.9)
        self.assertEqual(repository.matches, ("classification-run", [match]))

    async def test_match_persistence_failure_rolls_back(self) -> None:
        llmResult = LLMClassificationResult(
            guidelineResult=RelevanceResult.IRRELEVANT,
            motherhoodResult=RelevanceResult.IRRELEVANT,
        )
        similarityResult = SimilarityClassificationResult()

        class FakeLLMService:
            async def classify_article(self, content: str):
                return llmResult

        class FakeSimilarityService:
            async def classify_article(self, articleID: str):
                return similarityResult

        class FailingRepository:
            def __init__(self, db):
                pass

            async def create(self, data):
                return SimpleNamespace(id="classification-run")

            async def create_matches(self, classificationRunID, matches):
                raise RuntimeError("write failed")

        session = FakeSession()
        service = ClassificationService(
            sessionFactory=FakeSessionFactory(session),
            llmService=FakeLLMService(),
            similarityService=FakeSimilarityService(),
            settings=ClassificationSettings(),
        )

        with patch(
            "app.services.classificationService.ClassificationRunRepository",
            FailingRepository,
        ):
            with self.assertRaisesRegex(RuntimeError, "write failed"):
                await service.process_article("article", "content")

        self.assertFalse(session.committed)
        self.assertTrue(session.rolledBack)


class PipelineOrderingTests(unittest.IsolatedAsyncioTestCase):
    async def test_classification_starts_after_embeddings_finish(self) -> None:
        calls = []

        class FakeEmbeddingService:
            async def process_batch(self, batchID):
                calls.extend(["embedding-start", "embedding-finish"])

        class FakeClassificationService:
            async def process_batch(self, batchID):
                calls.append("classification-start")

        pipeline = PipelineService(
            batchService=SimpleNamespace(),
            articleService=SimpleNamespace(),
            articleEmbeddingService=FakeEmbeddingService(),
            classificationService=FakeClassificationService(),
        )

        await pipeline.run_workflows("batch")

        self.assertEqual(
            calls,
            ["embedding-start", "embedding-finish", "classification-start"],
        )


if __name__ == "__main__":
    unittest.main()
