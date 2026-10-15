from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ReviewerRole(StrEnum):
    ANALYST = "analyst"
    SUPERVISOR = "supervisor"
    MATERIALS_SPECIALIST = "materials_specialist"


class ReviewOutcome(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"
    REVISE = "revise"


class ReviewDecision(BaseModel):
    """Human review action for a recommendation. Uses a generic role, not a person."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    review_id: str = Field(min_length=1)
    recommendation_id: str = Field(min_length=1)
    reviewer_role: ReviewerRole
    decision: ReviewOutcome
    reason: str = Field(min_length=1)
    timestamp: datetime
