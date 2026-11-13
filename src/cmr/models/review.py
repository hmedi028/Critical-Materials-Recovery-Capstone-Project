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


# Used in:
# - src/cmr/demo_app.py human-review simulator (accept / reject / revise with a required reason)
# - src/cmr/generate_synthetic.py -> data/synthetic/review_decisions.json
# - src/cmr/export_schemas.py -> data/schemas/review_decision.json
# Review records are in-memory for the demo; they are not persisted
class ReviewDecision(BaseModel):
    """Human review action for a recommendation. Uses a generic role, not a person."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    review_id: str = Field(min_length=1)
    recommendation_id: str = Field(min_length=1)
    reviewer_role: ReviewerRole
    decision: ReviewOutcome
    reason: str = Field(min_length=1)
    timestamp: datetime
