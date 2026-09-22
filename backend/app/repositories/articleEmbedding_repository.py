from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.ArticleEmbedding_model import ArticleEmbedding


class ArticleEmbeddingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, articleEmbedding_id: str) -> ArticleEmbedding | None:
        stmt = select(ArticleEmbedding).where(ArticleEmbedding.id == articleEmbedding_id)

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> list[ArticleEmbedding]:
        stmt = (
            select(ArticleEmbedding)
            .offset(offset)
            .limit(limit)
            .order_by(ArticleEmbedding.created_at.desc())
        )

        result = await self.db.execute(stmt)

        return list(result.scalars().all())

    async def create(self, articleEmbedding: ArticleEmbedding) -> ArticleEmbedding:
        self.db.add(articleEmbedding)
        await self.db.flush()
        await self.db.refresh(articleEmbedding)

        return articleEmbedding

    async def delete(self, articleEmbedding: ArticleEmbedding) -> None:
        await self.db.delete(articleEmbedding)
        await self.db.flush()
    
    