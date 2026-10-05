from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.ArticleEmbedding_model import ArticleEmbedding
from ..models.Article_model import Article
from ..models.ClassificationMatch_model import ClassificationMatch
from ..models.ClassificationRun_model import ClassificationRun
from ..models.ProcessingBatch_model import ProcessingBatch
from ..models.Review_model import Review
from ..repositories.processingBatch_repository import ProcessingBatchRepository
from ..schemas.processingBatch_schema import (
    BatchArticleRead,
    ClassificationRead,
    GuidelineHitRead,
    ProcessingBatchCreate,
    ProcessingBatchDetail,
    ProcessingBatchSummary,
    ReviewRead,
    SimilarityMatchRead,
)
from ..models.enums import ProcessingStatus


class ProcessingBatchService:
    def __init__(self, db: AsyncSession, repository: ProcessingBatchRepository):
        self.db = db
        self.repository = repository

    async def create_batch(
        self,
        data: ProcessingBatchCreate,
        *,
        commit: bool = True,
    ) -> ProcessingBatch:
        batch = ProcessingBatch(
            filename=data.filename,
            status=ProcessingStatus.PROCESSING,
        )

        batch = await self.repository.create(batch)

        if commit:
            await self.db.commit()
            await self.db.refresh(batch)

        return batch

    @staticmethod
    def to_summary(batch: ProcessingBatch) -> ProcessingBatchSummary:
        return ProcessingBatchSummary(
            id=batch.id,
            fileName=batch.filename,
            status=batch.status,
            totalArticles=batch.total_articles,
            processedArticles=batch.processed_articles,
            createdAt=batch.created_at,
            completedAt=batch.completed_at,
        )

    async def fetch_latest_detail(self) -> ProcessingBatchDetail | None:
        batch = await self.repository.get_latest()
        if batch is None:
            return None

        return await self._build_detail(batch)

    async def fetch_detail(self, batchID: str) -> ProcessingBatchDetail | None:
        batch = await self.repository.get_by_id(batchID)
        if batch is None:
            return None

        return await self._build_detail(batch)

    async def _build_detail(self, batch: ProcessingBatch) -> ProcessingBatchDetail:
        articleResult = await self.db.execute(
            select(Article)
            .where(
                Article.processing_batch_id == batch.id,
                Article.deleted_at.is_(None),
            )
            .order_by(Article.created_at.asc(), Article.id.asc())
        )
        articles = list(articleResult.scalars().all())
        articleIDs = [article.id for article in articles]

        embeddingArticleIDs: set[str] = set()
        classificationsByArticle: dict[str, ClassificationRun] = {}
        matchesByRun: dict[str, list[SimilarityMatchRead]] = {}
        reviewsByRun: dict[str, ReviewRead] = {}

        if articleIDs:
            embeddingResult = await self.db.execute(
                select(ArticleEmbedding.article_id)
                .where(ArticleEmbedding.article_id.in_(articleIDs))
                .group_by(ArticleEmbedding.article_id)
            )
            embeddingArticleIDs = set(embeddingResult.scalars().all())

            rankedRuns = (
                select(
                    ClassificationRun.id.label("classification_run_id"),
                    func.row_number()
                    .over(
                        partition_by=ClassificationRun.article_id,
                        order_by=(
                            ClassificationRun.created_at.desc(),
                            ClassificationRun.id.desc(),
                        ),
                    )
                    .label("run_number"),
                )
                .where(ClassificationRun.article_id.in_(articleIDs))
                .subquery()
            )
            classificationResult = await self.db.execute(
                select(ClassificationRun)
                .join(
                    rankedRuns,
                    rankedRuns.c.classification_run_id == ClassificationRun.id,
                )
                .where(rankedRuns.c.run_number == 1)
            )
            classifications = list(classificationResult.scalars().all())
            classificationsByArticle = {
                classification.article_id: classification
                for classification in classifications
            }
            runIDs = [classification.id for classification in classifications]

            if runIDs:
                matchResult = await self.db.execute(
                    select(
                        ClassificationMatch,
                        Article.title,
                        Article.source_url,
                    )
                    .join(Article, Article.id == ClassificationMatch.matched_article_id)
                    .where(ClassificationMatch.classification_run_id.in_(runIDs))
                    .order_by(
                        ClassificationMatch.classification_run_id.asc(),
                        ClassificationMatch.similarity_score.desc(),
                        ClassificationMatch.matched_article_id.asc(),
                    )
                )
                for match, title, source in matchResult.all():
                    matchesByRun.setdefault(match.classification_run_id, []).append(
                        SimilarityMatchRead(
                            articleID=match.matched_article_id,
                            title=title,
                            source=source,
                            similarityScore=match.similarity_score,
                            relevanceResult=match.matched_decision,
                        )
                    )

                reviewResult = await self.db.execute(
                    select(Review).where(Review.classification_run_id.in_(runIDs))
                )
                reviewsByRun = {
                    review.classification_run_id: ReviewRead(
                        decision=review.decision,
                        remarks=review.remarks,
                        reviewedBy=review.reviewed_by,
                        reviewedAt=review.reviewed_at,
                    )
                    for review in reviewResult.scalars().all()
                }

        articleResponses: list[BatchArticleRead] = []
        for sequence, article in enumerate(articles, start=1):
            classification = classificationsByArticle.get(article.id)
            classificationResponse = None
            if classification is not None:
                guidelineHits = []
                rawGuidelineHits = (
                    classification.guideline_hits
                    if isinstance(classification.guideline_hits, list)
                    else []
                )
                for hit in rawGuidelineHits:
                    if not isinstance(hit, dict):
                        continue
                    guidelineID = hit.get("guidelineID") or hit.get("guideline_id")
                    reason = hit.get("reason")
                    if guidelineID and reason:
                        guidelineHits.append(
                            GuidelineHitRead(
                                guidelineID=str(guidelineID),
                                reason=str(reason),
                            )
                        )

                classificationResponse = ClassificationRead(
                    id=classification.id,
                    status=classification.status,
                    guidelineResult=classification.guideline_result,
                    guidelineReason=classification.guideline_reason,
                    guidelineHits=guidelineHits,
                    motherhoodResult=classification.motherhood_result,
                    motherhoodReason=classification.motherhood_reason,
                    similarityResult=classification.similarity_result,
                    confidenceScore=classification.confidence_score,
                    systemPrediction=classification.system_prediction,
                    llmModel=classification.llm_model,
                    embeddingModel=classification.embedding_model,
                    similarityMatches=matchesByRun.get(classification.id, []),
                    review=reviewsByRun.get(classification.id),
                )

            articleResponses.append(
                BatchArticleRead(
                    id=article.id,
                    sequence=sequence,
                    title=article.title,
                    content=article.content,
                    source=article.source_url,
                    publishedAt=article.published_at,
                    wordCount=len(article.content.split()),
                    embeddingComplete=article.id in embeddingArticleIDs,
                    classification=classificationResponse,
                )
            )

        totalArticles = len(articles)
        processedArticles = len(classificationsByArticle)
        effectiveStatus = batch.status
        if (
            effectiveStatus == ProcessingStatus.PROCESSING
            and batch.total_articles == 0
            and totalArticles > 0
            and processedArticles == totalArticles
        ):
            effectiveStatus = ProcessingStatus.PENDING_REVIEW

        return ProcessingBatchDetail(
            id=batch.id,
            fileName=batch.filename,
            status=effectiveStatus,
            totalArticles=totalArticles,
            processedArticles=processedArticles,
            createdAt=batch.created_at,
            completedAt=batch.completed_at,
            articles=articleResponses,
        )
