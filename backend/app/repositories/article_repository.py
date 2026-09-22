from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.Article_model import Article
from sqlalchemy.dialects.postgresql import insert


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

    async def create(self,article: Article,) -> Article | None: # not using ORM statement here because need to use on conflict method in case duplicate content hash is detected

        stmt = (
            insert(Article)
            .values(
                processing_batch_id=article.processing_batch_id,
                compilation_id=article.compilation_id,
                title=article.title,
                content=article.content,
                source_url=article.source_url,
                published_at=article.published_at,
                content_hash=article.content_hash,
            )
            .on_conflict_do_nothing(
                index_elements=[Article.content_hash]
            )
            .returning(Article)
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def delete(self, article: Article) -> None:
        await self.db.delete(article)
        await self.db.flush()
    
    