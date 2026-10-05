from pydantic import BaseModel, Field, model_validator

from ..models.enums import RelevanceResult, ProcessingStatus


class GuidelineHit(BaseModel):
    guidelineID: str = Field(
        description="Exact identifier of the matched guideline, without brackets.",
    )
    reason: str = Field(
        description="Concise article evidence explaining why this guideline matched.",
    )


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
    guidelineResult: RelevanceResult = Field(
        description=(
            "Relevant if and only if at least one relevance guideline matched."
        ),
    )
    guidelineReason: str | None = None
    guidelineHits: list[GuidelineHit] = Field(
        description=(
            "Required evidence list. Include one item for every matched guideline; "
            "use an empty list only when guidelineResult is irrelevant."
        ),
    )

    motherhoodResult: RelevanceResult
    motherhoodReason: str | None = None

    @model_validator(mode="after")
    def validate_guideline_consistency(self):
        if (
            self.guidelineResult == RelevanceResult.RELEVANT
            and not self.guidelineHits
        ):
            raise ValueError(
                "guidelineHits must contain at least one hit when guidelineResult is relevant"
            )

        if (
            self.guidelineResult == RelevanceResult.IRRELEVANT
            and self.guidelineHits
        ):
            raise ValueError(
                "guidelineHits must be empty when guidelineResult is irrelevant"
            )

        guidelineIDs = [hit.guidelineID for hit in self.guidelineHits]
        if len(guidelineIDs) != len(set(guidelineIDs)):
            raise ValueError("guidelineHits must not contain duplicate guideline IDs")

        return self
