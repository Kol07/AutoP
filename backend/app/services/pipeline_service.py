from ..schemas.article_schema import ArticleIngest, ArticleCreate
from ..schemas.processingBatch_schema import ProcessingBatchCreate
from .article_service import ArticleService
from .articleEmbedding_service import ArticleEmbeddingService
from .classificationService import ClassificationService
from .processingBatch_service import ProcessingBatchService


class PipelineService:
    def __init__(
        self,
        batchService: ProcessingBatchService,
        articleService: ArticleService,
        articleEmbeddingService: ArticleEmbeddingService,
        classificationService: ClassificationService,
    ):
        self.batchService = batchService
        self.articleService = articleService
        self.articleEmbeddingService = articleEmbeddingService
        self.classificationService = classificationService

    async def ingest_articles(
        self,
        fileName: str,
        articlesList: list[ArticleIngest],
    ):
        batchData = ProcessingBatchCreate(filename=fileName)
        batch = await self.batchService.create_batch(batchData)

        for article in articlesList:
            articleData = ArticleCreate(
                processingBatchID=batch.id,
                title=article.recordTitle,
                content=article.recordContent,
                source=article.recordSourceName,
                published_at=article.recordISOTimeStamp,
            )

            createdArticle = await self.articleService.create_article(articleData)

            if createdArticle is None:
                continue

        await self.run_workflows(batch.id)

        return batch

    async def run_workflows(self, batchID):
        await self.articleEmbeddingService.process_batch(batchID)
        await self.classificationService.process_batch(batchID)
