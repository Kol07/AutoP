import os
from dataclasses import dataclass
from math import isfinite


def _read_float(name: str, default: float) -> float:
    rawValue = os.getenv(name)
    try:
        return default if rawValue in (None, "") else float(rawValue)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc


def _read_int(name: str, default: int) -> int:
    rawValue = os.getenv(name)
    try:
        return default if rawValue in (None, "") else int(rawValue)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


@dataclass(frozen=True)
class ClassificationSettings:
    guidelineWeight: float = 0.60
    similarityWeight: float = 0.30
    motherhoodWeight: float = 0.10
    guidelineHitCap: int = 3
    similarityTopK: int = 5
    similarityMinimumScore: float = 0.70
    relevanceThreshold: float = 0.50
    classificationConcurrency: int = 10

    def __post_init__(self) -> None:
        weights = (
            self.guidelineWeight,
            self.similarityWeight,
            self.motherhoodWeight,
        )
        if any(not isfinite(weight) for weight in weights):
            raise ValueError("Classification weights must be finite")
        if any(weight < 0 for weight in weights):
            raise ValueError("Classification weights must be nonnegative")
        if self.guidelineWeight + self.motherhoodWeight <= 0:
            raise ValueError(
                "At least one always-available classification signal must have a positive weight"
            )
        if self.guidelineHitCap <= 0:
            raise ValueError("GUIDELINE_HIT_CAP must be greater than zero")
        if self.similarityTopK <= 0:
            raise ValueError("SIMILARITY_TOP_K must be greater than zero")
        if not isfinite(self.similarityMinimumScore) or not (
            0 <= self.similarityMinimumScore <= 1
        ):
            raise ValueError("SIMILARITY_MINIMUM_SCORE must be between 0 and 1")
        if not isfinite(self.relevanceThreshold) or not (
            0 <= self.relevanceThreshold <= 1
        ):
            raise ValueError(
                "CLASSIFICATION_RELEVANCE_THRESHOLD must be between 0 and 1"
            )
        if self.classificationConcurrency <= 0:
            raise ValueError("CLASSIFICATION_CONCURRENCY must be greater than zero")

    @classmethod
    def from_env(cls) -> "ClassificationSettings":
        return cls(
            guidelineWeight=_read_float("CLASSIFICATION_GUIDELINE_WEIGHT", 0.60),
            similarityWeight=_read_float(
                "CLASSIFICATION_SIMILARITY_WEIGHT",
                0.30,
            ),
            motherhoodWeight=_read_float(
                "CLASSIFICATION_MOTHERHOOD_WEIGHT",
                0.10,
            ),
            guidelineHitCap=_read_int("GUIDELINE_HIT_CAP", 3),
            similarityTopK=_read_int("SIMILARITY_TOP_K", 5),
            similarityMinimumScore=_read_float("SIMILARITY_MINIMUM_SCORE", 0.70),
            relevanceThreshold=_read_float(
                "CLASSIFICATION_RELEVANCE_THRESHOLD",
                0.50,
            ),
            classificationConcurrency=_read_int("CLASSIFICATION_CONCURRENCY", 10),
        )
