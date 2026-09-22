# app/dependencies.py

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .db.session import get_db

from .repositories.processingBatch_repository import (
    ProcessingBatchRepository,
)
from .repositories.article_repository import ArticleRepository

from .services.processingBatch_service import (
    ProcessingBatchService,
)
from .services.article_service import ArticleService
from .services.pipeline_service import PipelineService


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


def get_pipeline_service(
    batchService: ProcessingBatchService = Depends(
        get_processing_batch_service
    ),
    articleService: ArticleService = Depends(
        get_article_service
    ),
) -> PipelineService:

    return PipelineService(
        batchService=batchService,
        articleService=articleService,
    )