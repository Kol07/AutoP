from fastapi import APIRouter
from .health_route import router as health_router
from .articleProcessing_route import router as article_router

apiRouter = APIRouter(prefix="/api/v1")

apiRouter.include_router(health_router)
apiRouter.include_router(article_router)
