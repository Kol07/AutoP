from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from .db.session import get_db

from .repositories.processingBatch_repository import ProcessingBatchRepository
from .repositories.article_repository import ArticleRepository
from .repositories.articleEmbedding_repository import ArticleEmbeddingRepository

from .services.processingBatch_service import ProcessingBatchService
from .services.article_service import ArticleService
from .services.articleEmbedding_service import ArticleEmbeddingService
from .services.pipeline_service import PipelineService

import httpx


def get_processing_batch_service(
    db: AsyncSession = Depends(get_db),
) -> ProcessingBatchService:

    repository = ProcessingBatchRepository(db)

    return ProcessingBatchService(
        db=db,
        repository=repository,
    )


def get_article_service(
    db: AsyncSession = Depends(get_db),
) -> ArticleService:

    repository = ArticleRepository(db)

    return ArticleService(
        db=db,
        repository=repository,
    )

def get_http_client(
    request: Request,
) -> httpx.AsyncClient:
    return request.app.state.http_client

def get_article_embedding_service(
    db: AsyncSession = Depends(get_db),
    httpClient: httpx.AsyncClient = Depends(get_http_client)
) -> ArticleEmbeddingService:

    repository = ArticleEmbeddingRepository(db)

    return ArticleEmbeddingService(
        db=db,
        repository=repository,
        httpClient=httpClient
    )



def get_pipeline_service(
    batchService: ProcessingBatchService = Depends(
        get_processing_batch_service
    ),
    articleService: ArticleService = Depends(
        get_article_service
    ),
    articleEmbeddingService: ArticleEmbeddingService = Depends(
        get_article_embedding_service
    )
) -> PipelineService:

    return PipelineService(
        batchService=batchService,
        articleService=articleService,
        articleEmbeddingService= articleEmbeddingService
        )