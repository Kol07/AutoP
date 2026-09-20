from fastapi import APIRouter, Request

from ..schemas.article_schema import ArticleEmbedRequest
from ..services.article_service import embed_text

router = APIRouter(
    prefix = "/article",
    tags = ["Articles Flow"]
)

@router.post("/embed")
async def embed_article_route(request: Request, article: ArticleEmbedRequest):
    embedding = await embed_text(request, article.text)

    return {
        "embedding": embedding
    }