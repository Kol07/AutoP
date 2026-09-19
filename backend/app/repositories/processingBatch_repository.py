from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.ProcessingBatch_model import ProcessingBatch


class ProcessingBatchRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, processingBatch_id: str) -> ProcessingBatch | None:
        stmt = select(ProcessingBatch).where(ProcessingBatch.id == processingBatch_id)

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> list[ProcessingBatch]:
        stmt = (
            select(ProcessingBatch)
            .offset(offset)
            .limit(limit)
            .order_by(ProcessingBatch.created_at.desc())
        )

        result = await self.db.execute(stmt)

        return list(result.scalars().all())

    async def create(self, processingBatch: ProcessingBatch) -> ProcessingBatch:
        self.db.add(processingBatch)
        await self.db.flush()
        await self.db.refresh(processingBatch)

        return processingBatch

    async def delete(self, processingBatch: ProcessingBatch) -> None:
        await self.db.delete(processingBatch)
        await self.db.flush()
    
    