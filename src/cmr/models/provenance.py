from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class EvidenceQuality(StrEnum):
    CONFIRMED = "confirmed"
    INFERRED = "inferred"
    INCOMPLETE = "incomplete"
    CONFLICTING = "conflicting"


class Provenance(BaseModel):
    """Required source metadata for imported or generated records."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source_name: str = Field(min_length=1)
    source_url: HttpUrl | None = None
    source_record_id: str | None = Field(default=None, min_length=1)
    retrieved_date: date | None = None
    generated_date: date | None = None
    license_or_reuse_status: str = Field(min_length=1)
    evidence_quality: EvidenceQuality
    is_synthetic: bool

    @model_validator(mode="after")
    def require_source_identifier(self) -> "Provenance":
        if self.source_url is None and self.source_record_id is None:
            raise ValueError("Provide source_url or source_record_id")
        return self

    @model_validator(mode="after")
    def require_record_date(self) -> "Provenance":
        if self.retrieved_date is None and self.generated_date is None:
            raise ValueError("Provide retrieved_date or generated_date")
        return self
