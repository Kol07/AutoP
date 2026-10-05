from datetime import datetime

from pydantic import BaseModel, Field

from ..models.enums import ProcessingStatus, RelevanceResult
from .article_schema import ArticleIngest


class ProcessingBatchCreate(BaseModel):
    filename: str


class ProcessingBatchIngest(BaseModel):
    fileName: str = Field(min_length=1)
    articles: list[ArticleIngest] = Field(min_length=1)


class ProcessingBatchSummary(BaseModel):
    id: str
    fileName: str
    status: ProcessingStatus
    totalArticles: int
    processedArticles: int
    createdAt: datetime
    completedAt: datetime | None = None


class GuidelineHitRead(BaseModel):
    guidelineID: str
    reason: str


class SimilarityMatchRead(BaseModel):
    articleID: str
    title: str
    source: str | None = None
    similarityScore: float
    relevanceResult: RelevanceResult


class ReviewRead(BaseModel):
    decision: RelevanceResult
    remarks: str | None = None
    reviewedBy: str
    reviewedAt: datetime


class ClassificationRead(BaseModel):
    id: str
    status: ProcessingStatus
    guidelineResult: RelevanceResult
    guidelineReason: str | None = None
    guidelineHits: list[GuidelineHitRead] = Field(default_factory=list)
    motherhoodResult: RelevanceResult
    motherhoodReason: str | None = None
    similarityResult: RelevanceResult | None = None
    confidenceScore: float | None = None
    systemPrediction: RelevanceResult | None = None
    llmModel: str
    embeddingModel: str
    similarityMatches: list[SimilarityMatchRead] = Field(default_factory=list)
    review: ReviewRead | None = None


class BatchArticleRead(BaseModel):
    id: str
    sequence: int
    title: str
    content: str
    source: str | None = None
    publishedAt: datetime | None = None
    wordCount: int
    embeddingComplete: bool
    classification: ClassificationRead | None = None


class ProcessingBatchDetail(ProcessingBatchSummary):
    articles: list[BatchArticleRead] = Field(default_factory=list)
