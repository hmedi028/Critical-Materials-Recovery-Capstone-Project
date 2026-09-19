from pathlib import Path

from cmr.models.material import load_usgs_critical_minerals

REPO_ROOT = Path(__file__).resolve().parents[1]
USGS_CSV = REPO_ROOT / "data" / "static" / "usgs" / "critical_minerals_2025.csv"


def test_usgs_critical_minerals_csv_loads_60_materials() -> None:
    materials = load_usgs_critical_minerals(USGS_CSV)

    assert len(materials) == 60
    assert len({material.material_id for material in materials}) == 60
    assert sum(1 for material in materials if material.is_rare_earth_element) == 15
    assert all(not material.is_synthetic for material in materials)
    assert all(material.publication_year == 2025 for material in materials)
    assert all(
        material.to_criticality_reference().criticality_category
        == material.criticality_reference
        for material in materials
    )
