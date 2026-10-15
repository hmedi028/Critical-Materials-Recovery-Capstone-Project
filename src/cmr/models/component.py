from pydantic import Field

from cmr.models.provenance import Provenance


class Component(Provenance):
    """Generic component belonging to a public catalog item."""

    component_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    parent_item_id: str = Field(min_length=1)
    public_reference_number: str | None = Field(default=None, min_length=1)
