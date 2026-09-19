from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.Article_model import Article


class ArticleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, article_id: str) -> Article | None:
        stmt = select(Article).where(Article.id == article_id)

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Article]:
        stmt = (
            select(Article)
            .offset(offset)
            .limit(limit)
        )

        result = await self.db.execute(stmt)

        return list(result.scalars().all())

    async def create(self, article: Article) -> Article:
        self.db.add(article)
        await self.db.flush()
        await self.db.refresh(article)

        return article

    async def delete(self, article: Article) -> None:
        await self.db.delete(article)
        await self.db.flush()
    
    