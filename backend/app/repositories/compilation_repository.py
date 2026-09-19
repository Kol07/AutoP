from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.Compilation_model import Compilation


class CompilationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, compilation_id: str) -> Compilation | None:
        stmt = select(Compilation).where(Compilation.id == compilation_id)

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Compilation]:
        stmt = (
            select(Compilation)
            .offset(offset)
            .limit(limit)
        )

        result = await self.db.execute(stmt)

        return list(result.scalars().all())

    async def create(self, article: Compilation) -> Compilation:
        self.db.add(article)
        await self.db.flush()
        await self.db.refresh(article)

        return article

    async def delete(self, article: Compilation) -> None:
        await self.db.delete(article)
        await self.db.flush()
    
    async def get_by_id_with_articles(
        self,
        compilation_id: str,
    ) -> Compilation | None:
        stmt = (
            select(Compilation)
            .options(
                selectinload(Compilation.articles)
            )
            .where(
                Compilation.id == compilation_id,
                Compilation.deleted_at.is_(None),
            )
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()