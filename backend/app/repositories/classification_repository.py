from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.ClassificationRun_model import ClassificationRun
from ..models.ClassificationMatch_model import ClassificationMatch
from ..schemas.classification_schema import CreateClassificationRun
from ..schemas.similarity_schema import SimilarArticleMatch


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
            guideline_hits=[
                hit.model_dump()
                for hit in data.guidelineHits
            ],

            motherhood_result=data.motherhoodResult,
            motherhood_reason=data.motherhoodReason,

            similarity_result=data.similarityResult,
            confidence_score=data.confidenceScore,
            system_prediction=data.systemPrediction,

            llm_model=data.llmModel,
            embedding_model=data.embeddingModel,

            status=data.status,
        )

        self.db.add(classificationRun)

        await self.db.flush()
        await self.db.refresh(classificationRun)

        return classificationRun

    async def create_matches(
        self,
        classificationRunID: str,
        matches: list[SimilarArticleMatch],
    ) -> list[ClassificationMatch]:
        classificationMatches = [
            ClassificationMatch(
                classification_run_id=classificationRunID,
                matched_article_id=match.articleID,
                similarity_score=match.similarityScore,
                matched_decision=match.relevanceResult,
            )
            for match in matches
        ]

        self.db.add_all(classificationMatches)
        await self.db.flush()

        return classificationMatches

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
