from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.ClassificationRun_model import ClassificationRun
from ..schemas.classification_schema import CreateClassificationRun


class ClassificationRunRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        data: CreateClassificationRun,
    ) -> ClassificationRun:

        classificationRun = ClassificationRun(
            article_id=data.articleID,

            guideline_result=data.guidelineResult,
            guideline_reason=data.guidelineReason,
            guideline_hits = [
                hit.model_dump()
                for hit in data.guidelineHits
            ],

            motherhood_result=data.motherhoodResult,
            motherhood_reason=data.motherhoodReason,

            system_prediction=data.systemPrediction,

            llm_model=data.llmModel,
            embedding_model=data.embeddingModel,

            status=data.status,
        )

        self.db.add(classificationRun)

        await self.db.flush()
        await self.db.refresh(classificationRun)

        return classificationRun

    async def get_by_id(
        self,
        classificationRunID: str,
    ) -> ClassificationRun | None:

        result = await self.db.execute(
            select(ClassificationRun)
            .where(ClassificationRun.id == classificationRunID)
        )

        return result.scalar_one_or_none()

    async def get_by_article_id(
        self,
        articleID: str,
    ) -> ClassificationRun | None:

        result = await self.db.execute(
            select(ClassificationRun)
            .where(ClassificationRun.article_id == articleID)
        )

        return result.scalar_one_or_none()