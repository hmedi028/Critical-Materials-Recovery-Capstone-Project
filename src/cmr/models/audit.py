from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# Used in: 
# - src/cmr/recommend.py where an audit event is created for each recommendation
# - src/cmr/export_schemas.py where data is capable of export in json format
# - RecommendationReport -> displays the contents of the audit event object
class AuditEvent(BaseModel):
    """Analysis audit record. Must not contain PII, credentials, or operational logs."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    audit_id: str = Field(min_length=1)
    analysis_id: str = Field(min_length=1)
    action: str = Field(min_length=1)
    rules_executed: list[str] = Field(default_factory=list)
    timestamp: datetime
    result: str = Field(min_length=1)
