from datetime import date
from decimal import Decimal

from pydantic import Field

from cmr.models.provenance import Provenance


class ValueEstimate(Provenance):
    """Illustrative recovery value calculation. Not a live price quote."""

    estimate_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    quantity: Decimal = Field(gt=0)
    quantity_unit: str = Field(min_length=1)
    reference_value: Decimal = Field(ge=0)
    recovery_cost: Decimal = Field(ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    calculation_date: date
    is_illustrative: bool = True
