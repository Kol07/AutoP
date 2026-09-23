import os
import httpx
import asyncio

from ..schemas.article_schema import ArticleEmbeddingsCreate
from ..repositories.article_repository import ArticleRepository
from ..repositories.articleEmbedding_repository import ArticleEmbeddingRepository
from ..models.ArticleEmbedding_model import ArticleEmbedding

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

class ArticleEmbeddingService():
    def __init__(self, sessionFactory: async_sessionmaker[AsyncSession], httpClient: httpx.AsyncClient):
        
        self.sessionFactory = sessionFactory
        self.httpClient = httpClient
        
        self.semaphore = asyncio.Semaphore(
            int(os.getenv("EMBEDDING_CONCURRENCY", "10")) # 10 concurrent requests
        )
        
        self.embeddingURL = os.getenv(
            "VLLM_EMBED_URL",
            "http://192.168.2.2:7000") # fallback to testing server
        
        self.embeddingModel = os.getenv(
            "VLLM_EMBED_MODEL",
            "/models/qwen3-embedding-4b")
        
    async def create_embeddings(self, data: ArticleEmbeddingsCreate) -> ArticleEmbedding:
        async with self.sessionFactory() as db:
            
            repository = ArticleEmbeddingRepository(db)
            
            embeddings = ArticleEmbedding(
                article_id = data.articleID,
                model_name = data.modelName,
                model_revision = data.modelRevision,
                embedding = data.embedding,
                embedding_dimension = data.embeddingDimension
            )
            
            embeddings = await repository.create(embeddings)
            
            await db.commit()
            await db.refresh(embeddings)
            
            return embeddings

    async def embed_text(self, text: str) -> list[float]:
    
        
        response = await self.httpClient.post(
            f"{self.embeddingURL}/v1/embeddings",
            json={
                "input": text,
                "model": self.embeddingModel,
            },
        )

        response.raise_for_status()

        data = response.json()

        return data["data"][0]["embedding"]
    
    async def process_article(self, articleID, content: str):
        
        async with self.semaphore:
            
            embedding = await self.embed_text(content)
            
            embedding_data = ArticleEmbeddingsCreate(
                articleID=articleID,
                modelName= os.getenv("VLLM_EMBED_MODEL","/models/qwen3-embedding-4b"),
                modelRevision="v1 22092026",
                embedding=embedding,
                embeddingDimension=len(embedding)
            )
            
            await self.create_embeddings(
                embedding_data
            )
    
    async def process_batch(self, batchID):
        
        async with self.sessionFactory() as db:
            articleRepository = ArticleRepository(db)
            
            articles = await articleRepository.get_by_batch_id(
                batchID
            )
        
        article_data = [
            (article.id, article.content)
            for article in articles
        ]
        
        await asyncio.gather(
        *[
            self.process_article(
                article_id,
                content,
            )
            for article_id, content in article_data
        ]
        )