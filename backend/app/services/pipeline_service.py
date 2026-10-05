import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..models.enums import ProcessingStatus
from ..repositories.article_repository import ArticleRepository
from ..repositories.processingBatch_repository import ProcessingBatchRepository
from ..schemas.article_schema import ArticleIngest, ArticleCreate
from ..schemas.processingBatch_schema import ProcessingBatchCreate
from .article_service import ArticleService
from .articleEmbedding_service import ArticleEmbeddingService
from .classificationService import ClassificationService
from .processingBatch_service import ProcessingBatchService


logger = logging.getLogger(__name__)


class PipelineService:
    def __init__(
        self,
        batchService: ProcessingBatchService,
        articleService: ArticleService,
        articleEmbeddingService: ArticleEmbeddingService,
        classificationService: ClassificationService,
        sessionFactory: async_sessionmaker[AsyncSession],
    ):
        self.batchService = batchService
        self.articleService = articleService
        self.articleEmbeddingService = articleEmbeddingService
        self.classificationService = classificationService
        self.sessionFactory = sessionFactory

    async def create_ingest_batch(
        self,
        fileName: str,
        articlesList: list[ArticleIngest],
    ):
        batchData = ProcessingBatchCreate(filename=fileName)
        batch = await self.batchService.create_batch(batchData, commit=False)
        acceptedArticles = 0

        try:
            for article in articlesList:
                articleData = ArticleCreate(
                    processingBatchID=batch.id,
                    title=article.recordTitle,
                    content=article.recordContent,
                    source=article.recordSourceName,
                    published_at=article.recordISOTimeStamp,
                )

                createdArticle = await self.articleService.create_article(
                    articleData,
                    commit=False,
                )

                if createdArticle is not None:
                    acceptedArticles += 1

            batch.total_articles = acceptedArticles
            if acceptedArticles == 0:
                batch.status = ProcessingStatus.PENDING_REVIEW
                batch.completed_at = datetime.now(timezone.utc)

            await self.batchService.db.commit()
            await self.batchService.db.refresh(batch)
        except Exception:
            await self.batchService.db.rollback()
            raise

        return batch

    async def run_workflows(self, batchID):
        try:
            await self.articleEmbeddingService.process_batch(batchID)
            await self.classificationService.process_batch(batchID)
        except Exception:
            logger.exception("Processing batch %s failed", batchID)
            await self._finish_batch(batchID, ProcessingStatus.FAILED)
            return

        await self._finish_batch(batchID, ProcessingStatus.PENDING_REVIEW)

    async def _finish_batch(
        self,
        batchID: str,
        status: ProcessingStatus,
    ) -> None:
        async with self.sessionFactory() as db:
            batchRepository = ProcessingBatchRepository(db)
            articleRepository = ArticleRepository(db)
            batch = await batchRepository.get_by_id(batchID)
            if batch is None:
                logger.error("Cannot update missing processing batch %s", batchID)
                return

            batch.processed_articles = (
                await articleRepository.count_classified_by_batch_id(batchID)
            )
            batch.status = status
            batch.completed_at = datetime.now(timezone.utc)
            await db.commit()
