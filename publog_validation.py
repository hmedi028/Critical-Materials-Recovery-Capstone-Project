
from pathlib import Path
import pandas as pd

PROJECT = Path(__file__).resolve().parent
PROCESSED = PROJECT / "data" / "processed"


def read_csv(name):
    path = PROCESSED / name
    if not path.exists():
        print(f"MISSING FILE: {path}")
        return None
    return pd.read_csv(path, dtype={"NIIN": str})


def main():
    selected = read_csv("selected_niins.csv")
    evidence = read_csv("selected_material_evidence.csv")
    items = read_csv("selected_items.csv")
    identification = read_csv("selected_identification.csv")

    if any(df is None for df in [selected, evidence, items, identification]):
        print("\nValidation incomplete: one or more files are missing.")
        return

    print("PUB LOG PIPELINE VALIDATION")
    print("=" * 35)

    for name, df in [
        ("Selected NIINs", selected),
        ("Material evidence", evidence),
        ("Selected items", items),
        ("Selected identification", identification),
    ]:
        print(
            f"{name}: rows={len(df):,}; "
            f"unique NIINs={df['NIIN'].nunique():,}; "
            f"duplicate NIIN rows={df['NIIN'].duplicated().sum():,}"
        )

    selected_set = set(selected["NIIN"].dropna())
    evidence_set = set(evidence["NIIN"].dropna())
    item_set = set(items["NIIN"].dropna())
    identification_set = set(identification["NIIN"].dropna())

    specific = evidence[
        evidence["CRITICAL_MATERIAL"].notna()
        & evidence["CRITICAL_MATERIAL"].astype(str).str.strip().ne("")
    ]
    specific_set = set(specific["NIIN"].dropna())

    print("\nCONSISTENCY CHECKS")
    print("-" * 35)
    print("Selected NIINs missing from items:", len(selected_set - item_set))
    print(
        "Selected NIINs missing from identification:",
        len(selected_set - identification_set),
    )
    print("Item vs identification NIIN differences:", len(item_set ^ identification_set))
    print("Evidence NIINs not selected:", len(evidence_set - selected_set))
    print("Selected NIINs with specific material evidence:", len(selected_set & specific_set))
    print("Selected NIINs without specific material evidence:", len(selected_set - specific_set))

    required_text = ["REQUIREMENTS_STATEMENT", "CLEAR_TEXT_REPLY"]
    print("\nSOURCE-TEXT RETENTION")
    print("-" * 35)
    for column in required_text:
        if column in evidence.columns:
            nonempty = evidence[column].fillna("").astype(str).str.strip().ne("").sum()
            print(f"{column}: {nonempty:,} non-empty evidence rows")
        else:
            print(f"MISSING COLUMN: {column}")

    print("\nIMPORTANT LIMITATION")
    print("Material keyword matches are candidate evidence, not proof of composition")
    print("or recoverability. Identification codes are supporting indicators only.")


if __name__ == "__main__":
    main()
