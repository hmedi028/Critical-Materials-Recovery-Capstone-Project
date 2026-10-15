from decimal import Decimal

from pydantic import Field

from cmr.models.provenance import Provenance


class RecoveryMethod(Provenance):
    """Documented recovery process and expected yield for a material."""

    recovery_method_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    process_name: str = Field(min_length=1)
    expected_yield: Decimal = Field(ge=0, le=1)
    handling_notes: str | None = None
