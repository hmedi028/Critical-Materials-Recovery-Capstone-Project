from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import Self

from pydantic import Field, field_validator

from cmr.models.provenance import EvidenceQuality, Provenance

USGS_LICENSE_OR_REUSE_STATUS = (
    "USGS public information; confirm current redistribution terms before reuse"
)


class CriticalityReference(Provenance):
    """Versioned criticality assignment for a material."""

    material_id: str = Field(min_length=1)
    criticality_category: str = Field(min_length=1)
    publication: str = Field(min_length=1)
    publication_year: int
    version: str | None = None
    effective_date: date | None = None

    @field_validator("publication_year")
    @classmethod
    def publication_year_must_be_recent(cls, value: int) -> int:
        if value < 1900 or value > 2100:
            raise ValueError("publication_year must be a plausible four-digit year")
        return value


class Material(Provenance):
    """Material identity aligned with the USGS 2025 critical-minerals table."""

    material_id: str = Field(min_length=1)
    material_name: str = Field(min_length=1)
    material_category: str | None = None
    is_rare_earth_element: bool = False
    criticality_reference: str = Field(min_length=1)
    publication_year: int
    sort_order: int | None = None

    @field_validator("publication_year")
    @classmethod
    def publication_year_must_be_recent(cls, value: int) -> int:
        if value < 1900 or value > 2100:
            raise ValueError("publication_year must be a plausible four-digit year")
        return value

    def to_criticality_reference(self) -> CriticalityReference:
        return CriticalityReference(
            material_id=self.material_id,
            criticality_category=self.criticality_reference,
            publication=self.source_name,
            publication_year=self.publication_year,
            version=str(self.publication_year),
            effective_date=date(self.publication_year, 1, 1),
            source_name=self.source_name,
            source_url=self.source_url,
            source_record_id=self.source_record_id,
            retrieved_date=self.retrieved_date,
            generated_date=self.generated_date,
            license_or_reuse_status=self.license_or_reuse_status,
            evidence_quality=self.evidence_quality,
            is_synthetic=self.is_synthetic,
        )

    @classmethod
    def from_usgs_csv_row(cls, row: dict[str, str]) -> Self:
        return cls(
            material_id=row["material_id"],
            material_name=row["material_name"],
            criticality_reference=row["criticality_reference"],
            publication_year=int(row["publication_year"]),
            is_rare_earth_element=row["is_rare_earth_element"].strip().lower() == "true",
            source_name=row["source_name"],
            source_url=row["source_url"],
            retrieved_date=date.fromisoformat(row["retrieved_date"]),
            sort_order=int(row["sort_order"]),
            license_or_reuse_status=USGS_LICENSE_OR_REUSE_STATUS,
            evidence_quality=EvidenceQuality.CONFIRMED,
            is_synthetic=False,
        )


def load_usgs_critical_minerals(path: Path) -> list[Material]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [Material.from_usgs_csv_row(row) for row in csv.DictReader(handle)]
