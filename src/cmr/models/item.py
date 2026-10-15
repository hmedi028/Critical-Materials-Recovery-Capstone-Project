from pydantic import Field

from cmr.models.provenance import Provenance


class Item(Provenance):
    """Public catalog item used as the unit of analysis."""

    public_item_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    public_characteristics: dict[str, str] = Field(default_factory=dict)
