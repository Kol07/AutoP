from fastapi import APIRouter
from .health_route import router as health_router
from .processingBatch_route import router as processing_batch_router

apiRouter = APIRouter(prefix="/api/v1")

apiRouter.include_router(health_router)
apiRouter.include_router(processing_batch_router)
