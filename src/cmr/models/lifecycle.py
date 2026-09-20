from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import Field, model_validator

from cmr.models.provenance import Provenance


class LifecycleEventType(StrEnum):
    RECEIPT = "receipt"
    INSPECTION = "inspection"
    STORAGE = "storage"
    DISPOSITION = "disposition"


class ItemCondition(StrEnum):
    SERVICEABLE = "serviceable"
    UNSERVICEABLE = "unserviceable"
    DAMAGED = "damaged"
    UNKNOWN = "unknown"


class LifecycleEvent(Provenance):
    """Synthetic receipt, inspection, storage, or disposition event."""

    event_id: str = Field(min_length=1)
    item_id: str = Field(min_length=1)
    event_type: LifecycleEventType
    condition: ItemCondition
    quantity: Decimal = Field(gt=0)
    quantity_unit: str = Field(min_length=1)
    timestamp: datetime
    generic_location_code: str = Field(min_length=1)

    @model_validator(mode="after")
    def require_synthetic_event(self) -> "LifecycleEvent":
        if not self.is_synthetic:
            raise ValueError("Lifecycle events in this prototype must be synthetic")
        return self
