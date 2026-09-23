import os
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..services.articleLLM_service import ArticleLLMService

from ..repositories.article_repository import ArticleRepository
from ..repositories.classification_repository import ClassificationRunRepository

from ..schemas.classification_schema import (
    LLMClassificationResult,
    CreateClassificationRun,
)

from ..models.enums import (
    ProcessingStatus,
    RelevanceResult,
)


class ClassificationService:
    def __init__(
        self,
        sessionFactory: async_sessionmaker[AsyncSession],
        llmService: ArticleLLMService,
    ):
        self.sessionFactory = sessionFactory
        self.llmService = llmService

        self.llmModel = os.getenv(
            "VLLM_LLM_MODEL",
            "/models/qwen3.8-27B-FP8",
        )

        self.embeddingModel = os.getenv(
            "VLLM_EMBED_MODEL",
            "/models/qwen3-embedding-4b",
        )
    
    async def process_article(
        self,
        articleID: str,
        content: str,
    ):

        llmResult = await self.llmService.classify_article(
            content
        )

        systemPrediction = self._get_system_prediction(
            llmResult
        )

        classificationData = CreateClassificationRun(
            articleID=articleID,

            guidelineResult=llmResult.guidelineResult,
            guidelineReason=llmResult.guidelineReason,
            guidelineHits=llmResult.guidelineHits,

            motherhoodResult=llmResult.motherhoodResult,
            motherhoodReason=llmResult.motherhoodReason,

            systemPrediction=systemPrediction,

            llmModel=self.llmModel,
            embeddingModel=self.embeddingModel,

            status=ProcessingStatus.COMPLETED,
        )

        async with self.sessionFactory() as db:

            repository = ClassificationRunRepository(db)

            classificationRun = await repository.create(
                classificationData
            )

            await db.commit()

            return classificationRun
    
    async def process_batch(self, batchID: str,):

        async with self.sessionFactory() as db:

            articleRepository = ArticleRepository(db)

            articles = await articleRepository.get_by_batch_id(
                batchID
            )

            articleData = [
                (article.id, article.content)
                for article in articles
            ]

        await asyncio.gather(
            *[
                self.process_article(
                    articleID,
                    content,
                )
                for articleID, content in articleData
            ]
        )