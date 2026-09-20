from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuditEvent(BaseModel):
    """Analysis audit record. Must not contain PII, credentials, or operational logs."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    audit_id: str = Field(min_length=1)
    analysis_id: str = Field(min_length=1)
    action: str = Field(min_length=1)
    rules_executed: list[str] = Field(default_factory=list)
    timestamp: datetime
    result: str = Field(min_length=1)
