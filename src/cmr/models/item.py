from pydantic import Field

from cmr.models.provenance import Provenance

# Used in:
# - src/cmr/recommend.py as the unit of analysis for recommend_item()
# - src/cmr/test_cases.py and data/synthetic/test_cases.json (9-case benchmark)
# - src/cmr/reporting.py RecommendationReport and the Streamlit inspector
# - src/cmr/generate_synthetic.py / src/cmr/synthetic.py (100-item corpus)
# - src/cmr/export_schemas.py -> data/schemas/item.json
# Previous thin-slice demo loaded SYN-ITEM-002 from data/synthetic/items.json
class Item(Provenance):
    """Public catalog item used as the unit of analysis."""

    public_item_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    public_characteristics: dict[str, str] = Field(default_factory=dict)
