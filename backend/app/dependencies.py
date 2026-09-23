from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from .db.session import get_db, AsyncSessionLocal

from .repositories.processingBatch_repository import ProcessingBatchRepository
from .repositories.article_repository import ArticleRepository

from .services.processingBatch_service import ProcessingBatchService
from .services.article_service import ArticleService
from .services.articleEmbedding_service import ArticleEmbeddingService
from .services.articleLLM_service import ArticleLLMService
from .services.articleSimilarity_service import ArticleSimilarityService
from .services.classificationService import ClassificationService
from .services.pipeline_service import PipelineService

import httpx

## CRUD SERVICES
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
    
## END OF CRUD SERVICES

# WORKFLOW SERVICES 

"""
Due to the concurrent nature of the workflow services, multiple workflows may perform database operations at the same time.

For normal CRUD services, Depends(get_db) is used to provide an AsyncSession. Within a **single** FastAPI request, dependency results are cached by default. 
Therefore, if multiple services depend on the same get_db dependency, FastAPI will resolve it once and reuse the same AsyncSession across those services. 
This is desirable for normal sequential request handling because it avoids creating unnecessary sessions and allows related operations to share the same transaction context.

In a practical sense, db.flush() would then only work in the same AsyncSession as db.flush() only syncs pending changes within the current session transaction. Hence 
other DB operations in different sessions wont be able to see the changes until its committed.

However, a SQLAlchemy AsyncSession should not be used concurrently by multiple asyncio tasks. 
If two workflows run concurrently and both attempt to use the same request-scoped session, this can lead to session state and transaction issues.

Therefore, workflow services are given the AsyncSessionLocal session factory instead of a request-scoped AsyncSession. 
Each concurrent database task can then create and manage its own session as needed.

This ensures that concurrent workflow operations do not share the same AsyncSession and can interact with the database independently.
"""


def get_http_client(
    request: Request,
) -> httpx.AsyncClient:
    return request.app.state.http_client


def get_article_embedding_service(
    httpClient: httpx.AsyncClient = Depends(get_http_client),
) -> ArticleEmbeddingService:
    return ArticleEmbeddingService(
        sessionFactory=AsyncSessionLocal,
        httpClient=httpClient,
    )


def get_article_llm_service(
    httpClient: httpx.AsyncClient = Depends(get_http_client),
) -> ArticleLLMService:
    return ArticleLLMService(httpClient=httpClient)


def get_article_similarity_service() -> ArticleSimilarityService:
    return ArticleSimilarityService(sessionFactory=AsyncSessionLocal)


def get_classification_service(
    llmService: ArticleLLMService = Depends(get_article_llm_service),
    similarityService: ArticleSimilarityService = Depends(
        get_article_similarity_service
    ),
) -> ClassificationService:
    return ClassificationService(
        sessionFactory=AsyncSessionLocal,
        llmService=llmService,
        similarityService=similarityService,
    )


## END OF WORKFLOW SERVICES

def get_pipeline_service(
    batchService: ProcessingBatchService = Depends(
        get_processing_batch_service
    ),
    articleService: ArticleService = Depends(
        get_article_service
    ),
    articleEmbeddingService: ArticleEmbeddingService = Depends(
        get_article_embedding_service
    ),
    classificationService: ClassificationService = Depends(
        get_classification_service
    ),
) -> PipelineService:

    return PipelineService(
        batchService=batchService,
        articleService=articleService,
        articleEmbeddingService=articleEmbeddingService,
        classificationService=classificationService,
    )
