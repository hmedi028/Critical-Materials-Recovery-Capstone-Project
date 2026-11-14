from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class RecommendationCategory(StrEnum):
    RETAIN = "retain"
    RECLAIM = "reclaim"
    RECYCLE = "recycle"
    MANUAL_REVIEW = "manual_review"
    DISPOSE = "dispose"


# Used in:
# - src/cmr/recommend.py which creates the computed recommendation for each item
# - expected_recommendation on test cases (benchmark oracle only; the engine does not read it)
# - src/cmr/reporting.py RecommendationReport and Streamlit Summary / Detailed Analytics
# - src/cmr/export_schemas.py -> data/schemas/recommendation.json
# Previous Streamlit demo displayed expected_recommendation as the live result
# Previous thin-slice demo emitted a hardcoded Recommendation for SYN-ITEM-002
class Recommendation(BaseModel):
    """Classification outcome for a single item."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    recommendation_id: str = Field(min_length=1)
    item_id: str = Field(min_length=1)
    category: RecommendationCategory
    explanation: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    human_review_required: bool
