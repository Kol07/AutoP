import json

from .processingBatch_service import ProcessingBatchService
from .article_service import ArticleService
from ..schemas.article_schema import ArticleCreate
from ..schemas.processingBatch_schema import ProcessingBatchCreate

class PipelineService():
    def __init__(self, batchService: ProcessingBatchService, articleService: ArticleService):
        
        self.batchService = batchService
        self.articleService = articleService

    
    async def ingest_articles(self, fileName: str, articlesList: list[ArticleCreate]): # might change to zipfile
        
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
            
            await self.articleService.create_article(article_data)
            
            if article is None:
                continue
        
        # Workflow 1
        
        # Workflow 2
        
        # Workflow 3
        pass