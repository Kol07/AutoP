import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..models.enums import RelevanceResult
from ..repositories.articleEmbedding_repository import ArticleEmbeddingRepository
from ..schemas.similarity_schema import (
    SimilarArticleMatch,
    SimilarityClassificationResult,
)
from .classification_config import ClassificationSettings


class ArticleSimilarityService:
    def __init__(
        self,
        sessionFactory: async_sessionmaker[AsyncSession],
        settings: ClassificationSettings | None = None,
    ):
        self.sessionFactory = sessionFactory
        self.settings = settings or ClassificationSettings.from_env()
        self.embeddingModel = (
            os.getenv("VLLM_EMBED_MODEL") or "/models/qwen3-embedding-4b"
        )
        self.embeddingModelRevision = (
            os.getenv("VLLM_EMBED_MODEL_REVISION") or "v1 22092026"
        )

    async def classify_article(
        self,
        articleID: str,
    ) -> SimilarityClassificationResult:
        async with self.sessionFactory() as db:
            repository = ArticleEmbeddingRepository(db)
            target = await repository.get_for_article_model_revision(
                articleID,
                self.embeddingModel,
                self.embeddingModelRevision,
            )

            if target is None:
                raise ValueError(
                    f"No embedding found for article {articleID} using the configured model revision"
                )

            targetEmbedding, processingBatchID = target
            rows = await repository.find_reviewed_similar(
                targetEmbedding=targetEmbedding,
                excludedBatchID=processingBatchID,
                minimumScore=self.settings.similarityMinimumScore,
                limit=self.settings.similarityTopK,
            )

        matches = [
            SimilarArticleMatch(
                articleID=matchedArticleID,
                similarityScore=min(max(similarityScore, -1.0), 1.0),
                relevanceResult=decision,
            )
            for matchedArticleID, similarityScore, decision in rows
        ]

        return self._calculate_result(matches)

    def _calculate_result(
        self,
        matches: list[SimilarArticleMatch],
    ) -> SimilarityClassificationResult:
        if not matches:
            return SimilarityClassificationResult()

        totalSimilarity = sum(match.similarityScore for match in matches)
        if totalSimilarity <= 0:
            return SimilarityClassificationResult(matches=matches)

        relevantSimilarity = sum(
            match.similarityScore
            for match in matches
            if match.relevanceResult == RelevanceResult.RELEVANT
        )
        score = min(max(relevantSimilarity / totalSimilarity, 0.0), 1.0)
        result = (
            RelevanceResult.RELEVANT
            if score >= self.settings.relevanceThreshold
            else RelevanceResult.IRRELEVANT
        )

        return SimilarityClassificationResult(
            result=result,
            score=score,
            matches=matches,
        )
