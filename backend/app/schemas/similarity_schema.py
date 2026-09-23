from pydantic import BaseModel, Field

from ..models.enums import RelevanceResult


class SimilarArticleMatch(BaseModel):
    articleID: str
    similarityScore: float = Field(ge=-1, le=1, allow_inf_nan=False)
    relevanceResult: RelevanceResult


class SimilarityClassificationResult(BaseModel):
    result: RelevanceResult | None = None
    score: float | None = Field(
        default=None,
        ge=0,
        le=1,
        allow_inf_nan=False,
    )
    matches: list[SimilarArticleMatch] = Field(default_factory=list)
