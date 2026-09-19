from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class RecommendationCategory(StrEnum):
    RETAIN = "retain"
    RECLAIM = "reclaim"
    RECYCLE = "recycle"
    MANUAL_REVIEW = "manual_review"
    DISPOSE = "dispose"


class Recommendation(BaseModel):
    """Classification outcome for a single item."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    item_id: str = Field(min_length=1)
    category: RecommendationCategory
    explanation: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    human_review_required: bool
