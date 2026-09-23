from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.Article_model import Article
from ..models.ArticleEmbedding_model import ArticleEmbedding
from ..models.ClassificationRun_model import ClassificationRun
from ..models.Review_model import Review
from ..models.enums import RelevanceResult


class ArticleEmbeddingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, articleEmbedding_id: str) -> ArticleEmbedding | None:
        stmt = select(ArticleEmbedding).where(ArticleEmbedding.id == articleEmbedding_id)

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> list[ArticleEmbedding]:
        stmt = (
            select(ArticleEmbedding)
            .offset(offset)
            .limit(limit)
            .order_by(ArticleEmbedding.created_at.desc())
        )

        result = await self.db.execute(stmt)

        return list(result.scalars().all())

    async def create(self, articleEmbedding: ArticleEmbedding) -> ArticleEmbedding:
        self.db.add(articleEmbedding)
        await self.db.flush()
        await self.db.refresh(articleEmbedding)

        return articleEmbedding

    async def get_for_article_model_revision(
        self,
        articleID: str,
        modelName: str,
        modelRevision: str,
    ) -> tuple[ArticleEmbedding, str] | None:
        stmt = (
            select(ArticleEmbedding, Article.processing_batch_id)
            .join(Article, Article.id == ArticleEmbedding.article_id)
            .where(
                ArticleEmbedding.article_id == articleID,
                ArticleEmbedding.model_name == modelName,
                ArticleEmbedding.model_revision == modelRevision,
            )
        )

        result = await self.db.execute(stmt)
        row = result.one_or_none()

        if row is None:
            return None

        return row[0], row[1]

    async def find_reviewed_similar(
        self,
        *,
        targetEmbedding: ArticleEmbedding,
        excludedBatchID: str,
        minimumScore: float,
        limit: int,
    ) -> list[tuple[str, float, RelevanceResult]]:
        latestReview = (
            select(
                ClassificationRun.article_id.label("article_id"),
                Review.decision.label("decision"),
                func.row_number()
                .over(
                    partition_by=ClassificationRun.article_id,
                    order_by=(Review.reviewed_at.desc(), Review.id.desc()),
                )
                .label("review_number"),
            )
            .join(
                Review,
                Review.classification_run_id == ClassificationRun.id,
            )
            .subquery()
        )

        cosineDistance = ArticleEmbedding.embedding.cosine_distance(
            targetEmbedding.embedding
        )
        similarityScore = (1 - cosineDistance).label("similarity_score")

        stmt = (
            select(
                ArticleEmbedding.article_id,
                similarityScore,
                latestReview.c.decision,
            )
            .join(Article, Article.id == ArticleEmbedding.article_id)
            .join(latestReview, latestReview.c.article_id == Article.id)
            .where(
                Article.processing_batch_id != excludedBatchID,
                Article.deleted_at.is_(None),
                ArticleEmbedding.model_name == targetEmbedding.model_name,
                ArticleEmbedding.model_revision == targetEmbedding.model_revision,
                ArticleEmbedding.embedding_dimension
                == targetEmbedding.embedding_dimension,
                latestReview.c.review_number == 1,
                similarityScore >= minimumScore,
            )
            .order_by(cosineDistance.asc(), ArticleEmbedding.article_id.asc())
            .limit(limit)
        )

        result = await self.db.execute(stmt)

        return [
            (row.article_id, float(row.similarity_score), row.decision)
            for row in result.all()
        ]

    async def delete(self, articleEmbedding: ArticleEmbedding) -> None:
        await self.db.delete(articleEmbedding)
        await self.db.flush()
    
