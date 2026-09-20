from ..models.ProcessingBatch_model import ProcessingBatch
from ..repositories.processingBatch_repository import ProcessingBatchRepository
from ..schemas.processingBatch_schema import ProcessingBatchCreate

from ..models.enums import ProcessingStatus

from sqlalchemy.ext.asyncio import AsyncSession

class ProcessingBatchService:
    def __init__(self, db: AsyncSession, repository: ProcessingBatchRepository,):
        
        self.db = db
        self.repository = repository

    async def create_batch(self, data: ProcessingBatchCreate,) -> ProcessingBatch:
        batch = ProcessingBatch(
            filename = data.filename,
            status = ProcessingStatus.PROCESSING
        )

        batch = await self.repository.create(batch)

        await self.db.commit()
        await self.db.refresh(batch)

        return batch