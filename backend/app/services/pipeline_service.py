from .processingBatch_service import ProcessingBatchService
from .article_service import ArticleService
from .articleEmbedding_service import ArticleEmbeddingService
from .classificationService import ClassificationService
from ..schemas.article_schema import ArticleIngest, ArticleCreate
from ..schemas.processingBatch_schema import ProcessingBatchCreate

import asyncio

class PipelineService():
    def __init__(self, batchService: ProcessingBatchService, articleService: ArticleService, articleEmbeddingService: ArticleEmbeddingService):
        
        self.batchService = batchService
        self.articleService = articleService
        self.articleEmbeddingService = articleEmbeddingService

    
    async def ingest_articles(self, fileName: str, articlesList: list[ArticleIngest]): # might change to zipfile
        
        batch_data = ProcessingBatchCreate(filename=fileName)
        batch = await self.batchService.create_batch(batch_data)        
        
        for article in articlesList:
            
            article_data = ArticleCreate(
                processingBatchID = batch.id,
                title = article.recordTitle,
                content = article.recordContent,
                source = article.recordSourceName,
                published_at = article.recordISOTimeStamp
                
            )
            
            created_article = await self.articleService.create_article(article_data)
            
            if created_article is None:
                continue
        
        
        await self.run_workflows(batch.id)
        
        return batch
    
    async def run_workflows(self, batchID):
        
        await asyncio.gather(

            self.articleEmbeddingService.process_batch(batchID)
            
            
        )