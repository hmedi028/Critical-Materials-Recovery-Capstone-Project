from decimal import Decimal
from enum import StrEnum

from pydantic import Field, model_validator

from cmr.models.provenance import Provenance


class EvidenceType(StrEnum):
    SPECIFICATION = "specification"
    PUBLIC_DATASET = "public_dataset"
    SYNTHETIC_BOM = "synthetic_bom"
    INFERRED = "inferred"


class ValueBasis(StrEnum):
    CONFIRMED = "confirmed"
    INFERRED = "inferred"
    SYNTHETIC = "synthetic"


class CompositionEvidence(Provenance):
    """Material assertion for an item or component, with units and value basis."""

    item_id: str | None = Field(default=None, min_length=1)
    component_id: str | None = Field(default=None, min_length=1)
    material_id: str = Field(min_length=1)
    quantity: Decimal | None = Field(default=None, gt=0)
    quantity_unit: str | None = Field(default=None, min_length=1)
    percentage: Decimal | None = Field(default=None, ge=0, le=100)
    evidence_type: EvidenceType
    value_basis: ValueBasis

    @model_validator(mode="after")
    def require_subject(self) -> "CompositionEvidence":
        if self.item_id is None and self.component_id is None:
            raise ValueError("Provide item_id or component_id")
        return self

    @model_validator(mode="after")
    def require_measured_amount(self) -> "CompositionEvidence":
        has_quantity = self.quantity is not None
        has_unit = self.quantity_unit is not None
        if has_quantity != has_unit:
            raise ValueError("quantity and quantity_unit must be provided together")
        if not has_quantity and self.percentage is None:
            raise ValueError("Provide quantity with quantity_unit, or percentage")
        return self

    @model_validator(mode="after")
    def synthetic_basis_matches_flag(self) -> "CompositionEvidence":
        if self.value_basis is ValueBasis.SYNTHETIC and not self.is_synthetic:
            raise ValueError("Synthetic composition evidence must set is_synthetic=True")
        if self.value_basis is ValueBasis.CONFIRMED and self.is_synthetic:
            raise ValueError("Confirmed composition evidence cannot be synthetic")
        return self
