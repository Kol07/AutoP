from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from ..dependencies import get_pipeline_service, get_processing_batch_service
from ..models.enums import ProcessingStatus
from ..schemas.processingBatch_schema import (
    ProcessingBatchDetail,
    ProcessingBatchIngest,
    ProcessingBatchSummary,
)
from ..services.pipeline_service import PipelineService
from ..services.processingBatch_service import ProcessingBatchService


router = APIRouter(
    prefix="/processing-batches",
    tags=["Processing batches"],
)


@router.post(
    "",
    response_model=ProcessingBatchSummary,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_processing_batch(
    request: ProcessingBatchIngest,
    backgroundTasks: BackgroundTasks,
    pipelineService: PipelineService = Depends(get_pipeline_service),
):
    batch = await pipelineService.create_ingest_batch(
        fileName=request.fileName,
        articlesList=request.articles,
    )

    if batch.status == ProcessingStatus.PROCESSING:
        backgroundTasks.add_task(pipelineService.run_workflows, batch.id)

    return ProcessingBatchService.to_summary(batch)


@router.get("/latest", response_model=ProcessingBatchDetail)
async def get_latest_processing_batch(
    batchService: ProcessingBatchService = Depends(get_processing_batch_service),
):
    batch = await batchService.fetch_latest_detail()
    if batch is None:
        raise HTTPException(status_code=404, detail="No processing batch found")

    return batch


@router.get("/{batchID}", response_model=ProcessingBatchDetail)
async def get_processing_batch(
    batchID: str,
    batchService: ProcessingBatchService = Depends(get_processing_batch_service),
):
    batch = await batchService.fetch_detail(batchID)
    if batch is None:
        raise HTTPException(status_code=404, detail="Processing batch not found")

    return batch
