from pydantic import BaseModel, ConfigDict
from ..models.enums import RelevanceResult, ProcessingStatus

class GuidelineHit(BaseModel):
    guidelineID: str
    reason: str

class CreateClassificationRun(BaseModel):
    articleID: str

    guidelineResult: RelevanceResult
    guidelineReason: str | None = None
    guidelineHits: list[GuidelineHit] = []

    motherhoodResult: RelevanceResult
    motherhoodReason: str | None = None

    systemPrediction: RelevanceResult

    llmModel: str
    embeddingModel: str

    status: ProcessingStatus

class LLMClassificationResult(BaseModel):
    guidelineResult: RelevanceResult
    guidelineReason: str | None = None
    guidelineHits: list[GuidelineHit] = []

    motherhoodResult: RelevanceResult
    motherhoodReason: str | None = None
    