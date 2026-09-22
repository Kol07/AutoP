from fastapi import APIRouter, Request, Depends

from ..schemas.article_schema import ArticleEmbedRequest, ArticleIngest
from ..services.article_service import ArticleService

from ..services.pipeline_service import PipelineService
from ..dependencies import get_pipeline_service

router = APIRouter(
    prefix = "/article",
    tags = ["Articles Flow"]
)

@router.post("/article_json_ingest")
async def article_json_ingest_route(articles: list[ArticleIngest], pipelineService: PipelineService = Depends (get_pipeline_service)):
    return await pipelineService.ingest_articles(fileName="tempfile.json", articlesList=articles)
    

## To fix this route later to fit into new coding practices
@router.post("/embed")
async def embed_article_route(request: Request, article: ArticleEmbedRequest):
    embedding = await ArticleService.embed_text(request, article.text)

    return {
        "embedding": embedding
    }