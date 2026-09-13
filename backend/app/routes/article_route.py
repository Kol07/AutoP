from fastapi import APIRouter

from ..schemas.article_schema import ArticleEmbedRequest
from ..services.embedArticle_service import embed_text

router = APIRouter(
    prefix = "/article",
    tags = ["Articles Flow"]
)

@router.post("/embed")
async def embed_article_route(article: ArticleEmbedRequest):
    embedding = await embed_text(article.text)

    return {
        "embedding": embedding
    }