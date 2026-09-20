import os
from fastapi import Request
import hashlib

from ..schemas.article_schema import ArticleCreate
from ..repositories.article_repository import ArticleRepository
from ..models.Article_model import Article

from sqlalchemy.ext.asyncio import AsyncSession

class ArticleService():
    def __init__(self, db: AsyncSession, repository: ArticleRepository):
        
        self.db = db
        self.repository = repository
        

    async def create_article(self, data: ArticleCreate) -> Article:
        
        hashed_content = hashlib.blake2b(data.content.encode("utf-8"),
                                         digest_size=16).hexdigest()
        
        article = Article(
            processing_batch_id = data.processingBatchID,
            title = data.title,
            content = data.content,
            source_url = data.source,
            published_at = data.published_at,
            content_hash = hashed_content
        )
        
        article = await self.repository.create(article)
        
        await self.db.commit()
        await self.db.refresh(article)
        
        return article

    async def embed_text(request: Request, text: str) -> list[float]:
        
        VLLM_EMBED_URL = os.getenv("VLLM_EMBED_URL","http://192.168.2.2:7000") # fallback to testing server
        VLLM_EMBED_MODEL = os.getenv("VLLM_EMBED_MODEL","/models/qwen3-embedding-4b")
        
        client = request.app.state.http_client
        
        response = await client.post(
            f"{VLLM_EMBED_URL}/v1/embeddings",
            json={
                "input": text,
                "model": VLLM_EMBED_MODEL,
            },
        )

        response.raise_for_status()

        data = response.json()

        return data["data"][0]["embedding"]