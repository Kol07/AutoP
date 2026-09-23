import asyncio
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..services.articleLLM_service import ArticleLLMService
from ..services.articleSimilarity_service import ArticleSimilarityService
from ..services.classification_config import ClassificationSettings

from ..repositories.article_repository import ArticleRepository
from ..repositories.classification_repository import ClassificationRunRepository

from ..schemas.classification_schema import (
    CreateClassificationRun,
    LLMClassificationResult,
)
from ..schemas.similarity_schema import SimilarityClassificationResult

from ..models.enums import (
    ProcessingStatus,
    RelevanceResult,
)


class ClassificationService:
    def __init__(
        self,
        sessionFactory: async_sessionmaker[AsyncSession],
        llmService: ArticleLLMService,
        similarityService: ArticleSimilarityService,
        settings: ClassificationSettings | None = None,
    ):
        self.sessionFactory = sessionFactory
        self.llmService = llmService
        self.similarityService = similarityService
        self.settings = settings or ClassificationSettings.from_env()
        self.semaphore = asyncio.Semaphore(self.settings.classificationConcurrency)

        self.llmModel = (
            os.getenv("VLLM_LLM_MODEL") or "/models/qwen3.8-27B-FP8"
        )

        self.embeddingModel = (
            os.getenv("VLLM_EMBED_MODEL") or "/models/qwen3-embedding-4b"
        )
    
    async def process_article(
        self,
        articleID: str,
        content: str,
    ):
        async with self.semaphore:
            return await self._process_article(articleID, content)

    async def _process_article(
        self,
        articleID: str,
        content: str,
    ):
        llmResult, similarityResult = await asyncio.gather(
            self.llmService.classify_article(content),
            self.similarityService.classify_article(articleID),
        )

        confidenceScore = self._calculate_confidence(
            llmResult,
            similarityResult,
        )
        systemPrediction = self._get_system_prediction(confidenceScore)

        classificationData = CreateClassificationRun(
            articleID=articleID,

            guidelineResult=llmResult.guidelineResult,
            guidelineReason=llmResult.guidelineReason,
            guidelineHits=llmResult.guidelineHits,

            motherhoodResult=llmResult.motherhoodResult,
            motherhoodReason=llmResult.motherhoodReason,

            similarityResult=similarityResult.result,
            confidenceScore=confidenceScore,
            systemPrediction=systemPrediction,

            llmModel=self.llmModel,
            embeddingModel=self.embeddingModel,

            status=ProcessingStatus.PENDING_REVIEW,
        )

        async with self.sessionFactory() as db:
            repository = ClassificationRunRepository(db)

            try:
                classificationRun = await repository.create(classificationData)
                await repository.create_matches(
                    classificationRun.id,
                    similarityResult.matches,
                )

                await db.commit()

                return classificationRun
            except Exception:
                await db.rollback()
                raise

    def _calculate_confidence(
        self,
        llmResult: LLMClassificationResult,
        similarityResult: SimilarityClassificationResult,
    ) -> float:
        guidelineScore = 0.0
        if llmResult.guidelineResult == RelevanceResult.RELEVANT:
            guidelineScore = min(
                len(llmResult.guidelineHits) / self.settings.guidelineHitCap,
                1.0,
            )

        motherhoodScore = (
            1.0
            if llmResult.motherhoodResult == RelevanceResult.RELEVANT
            else 0.0
        )

        weightedSignals = [
            (self.settings.guidelineWeight, guidelineScore),
            (self.settings.motherhoodWeight, motherhoodScore),
        ]
        if similarityResult.score is not None:
            weightedSignals.append(
                (self.settings.similarityWeight, similarityResult.score)
            )

        activeWeight = sum(weight for weight, _ in weightedSignals)
        confidenceScore = sum(
            weight * score for weight, score in weightedSignals
        ) / activeWeight

        return min(max(confidenceScore, 0.0), 1.0)

    def _get_system_prediction(
        self,
        confidenceScore: float,
    ) -> RelevanceResult:
        return (
            RelevanceResult.RELEVANT
            if confidenceScore >= self.settings.relevanceThreshold
            else RelevanceResult.IRRELEVANT
        )

    async def process_batch(self, batchID: str):
        async with self.sessionFactory() as db:
            articleRepository = ArticleRepository(db)
            articles = await articleRepository.get_by_batch_id(batchID)

            articleData = [
                (article.id, article.content)
                for article in articles
            ]

        await asyncio.gather(
            *[
                self.process_article(articleID, content)
                for articleID, content in articleData
            ]
        )
