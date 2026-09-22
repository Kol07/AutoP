import os
import httpx

from ..schemas.article_schema import ArticleEmbeddingsCreate
from ..repositories.articleEmbedding_repository import ArticleEmbeddingRepository
from ..models.ArticleEmbedding_model import ArticleEmbedding

from sqlalchemy.ext.asyncio import AsyncSession

class ArticleEmbeddingService():
    def __init__(self, db: AsyncSession, repository: ArticleEmbeddingRepository, httpClient: httpx.AsyncClient):
        
        self.db = db
        self.repository = repository
        self.httpClient = httpClient
    
    async def create_embeddings(self, data: ArticleEmbeddingsCreate) -> ArticleEmbedding:
        embeddings = ArticleEmbedding(
            article_id = data.articleID,
            model_name = data.modelName,
            model_revision = data.modelRevision,
            embedding = data.embedding,
            embedding_dimension = data.embeddingDimension
        )
        
        embeddings = await self.repository.create(embeddings)
        
        await self.db.commit()
        await self.db.refresh(embeddings)
        
        return embeddings

    async def embed_text(self, text: str) -> list[float]:
        
        VLLM_EMBED_URL = os.getenv("VLLM_EMBED_URL","http://192.168.2.2:7000") # fallback to testing server
        VLLM_EMBED_MODEL = os.getenv("VLLM_EMBED_MODEL","/models/qwen3-embedding-4b")
        
        response = await self.httpClient.post(
            f"{VLLM_EMBED_URL}/v1/embeddings",
            json={
                "input": text,
                "model": VLLM_EMBED_MODEL,
            },
        )

        response.raise_for_status()

        data = response.json()

        return data["data"][0]["embedding"]