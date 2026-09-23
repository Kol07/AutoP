from pydantic import BaseModel, Field

from ..models.enums import RelevanceResult, ProcessingStatus


class GuidelineHit(BaseModel):
    guidelineID: str
    reason: str


class CreateClassificationRun(BaseModel):
    articleID: str

    guidelineResult: RelevanceResult
    guidelineReason: str | None = None
    guidelineHits: list[GuidelineHit] = Field(default_factory=list)

    motherhoodResult: RelevanceResult
    motherhoodReason: str | None = None
    similarityResult: RelevanceResult | None = None
    confidenceScore: float = Field(ge=0, le=1, allow_inf_nan=False)
    systemPrediction: RelevanceResult

    llmModel: str
    embeddingModel: str

    status: ProcessingStatus


class LLMClassificationResult(BaseModel):
    guidelineResult: RelevanceResult
    guidelineReason: str | None = None
    guidelineHits: list[GuidelineHit] = Field(default_factory=list)

    motherhoodResult: RelevanceResult
    motherhoodReason: str | None = None
