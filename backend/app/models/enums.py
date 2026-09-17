from enum import StrEnum

from sqlalchemy import Enum


class RelevanceResult(StrEnum):
    RELEVANT = "relevant"
    IRRELEVANT = "irrelevant"


class ProcessingStatus(StrEnum):
    PROCESSING = "processing"
    PENDING_REVIEW = "pending_review"
    REVIEWED = "reviewed"
    FAILED = "failed"


def _enum_values(enum_class: type[StrEnum]) -> list[str]:
    return [member.value for member in enum_class]


RELEVANCE_RESULT_ENUM = Enum(
    RelevanceResult,
    name="relevance_result",
    native_enum=True,
    validate_strings=True,
    values_callable=_enum_values,
)

PROCESSING_STATUS_ENUM = Enum(
    ProcessingStatus,
    name="processing_status",
    native_enum=True,
    validate_strings=True,
    values_callable=_enum_values,
)
