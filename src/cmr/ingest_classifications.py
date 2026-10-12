"""Priority 4: join selected items to H2/H6 classification lookups.

Translates FSC, FSG, and INC on the thin-slice selected_items.csv using
local source lookup files. Lookups describe item type, not material
composition. Unmatched codes are documented; items are not dropped.

Run:
    python -m cmr.ingest_classifications
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

DEFAULT_ITEMS = PROCESSED_DIR / "selected_items.csv"
DEFAULT_FSG = RAW_DIR / "V_H2_FSG.CSV"
DEFAULT_FSC = RAW_DIR / "V_H2_FSC.CSV"
DEFAULT_INC = RAW_DIR / "V_H6_NAME_INC.CSV"
DEFAULT_CLASSIFIED = PROCESSED_DIR / "selected_items_classified.csv"
DEFAULT_GROUPS = PROCESSED_DIR / "classification_groups.csv"
DEFAULT_UNMATCHED = PROCESSED_DIR / "classification_unmatched.csv"

CLASSIFIED_FIELDS = (
    "NIIN",
    "NSN",
    "ITEM_NAME",
    "END_ITEM_NAME",
    "FSC",
    "FSG",
    "FSG_TITLE",
    "FSC_TITLE",
    "INC",
    "INC_DEFINITION",
)
GROUP_FIELDS = (
    "FSG",
    "FSG_TITLE",
    "FSC",
    "FSC_TITLE",
    "INC",
    "item_count",
)
UNMATCHED_FIELDS = ("NIIN", "code_type", "code", "reason")


def _text(row: dict[str, str | None], *names: str) -> str:
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def load_csv_by_key(path: Path, key: str) -> tuple[dict[str, dict[str, str]], int]:
    table: dict[str, dict[str, str]] = {}
    rows_read = 0
    with path.open(encoding="utf-8", errors="replace", newline="") as handle:
        for row in csv.DictReader(handle):
            rows_read += 1
            code = _text(row, key)
            if code and code not in table:
                table[code] = {name: (value or "").strip() for name, value in row.items()}
    return table, rows_read


def load_inc_lookups(path: Path, needed: set[str]) -> tuple[dict[str, dict[str, str]], int]:
    table: dict[str, dict[str, str]] = {}
    rows_read = 0
    with path.open(encoding="utf-8", errors="replace", newline="") as handle:
        for row in csv.DictReader(handle):
            rows_read += 1
            code = _text(row, "INC")
            if code in needed and code not in table:
                table[code] = {name: (value or "").strip() for name, value in row.items()}
                if len(table) == len(needed):
                    break
    return table, rows_read


def classify_items(
    items: list[dict[str, str]],
    fsg_lookup: dict[str, dict[str, str]],
    fsc_lookup: dict[str, dict[str, str]],
    inc_lookup: dict[str, dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    classified: list[dict[str, str]] = []
    unmatched: list[dict[str, str]] = []

    for item in items:
        fsc = _text(item, "FSC")
        inc = _text(item, "INC")
        niin = _text(item, "NIIN")
        fsg = fsc[:2] if len(fsc) >= 2 else ""
        fsg_row = fsg_lookup.get(fsc)
        fsc_row = fsc_lookup.get(fsc)
        inc_row = inc_lookup.get(inc)
        fsg_title = _text(fsg_row, "FSG_TITLE") if fsg_row else ""
        fsc_title = _text(fsc_row, "FSC_TITLE") if fsc_row else ""
        inc_definition = _text(inc_row, "DEFINITION") if inc_row else ""

        classified.append(
            {
                "NIIN": niin,
                "NSN": _text(item, "NSN"),
                "ITEM_NAME": _text(item, "ITEM_NAME"),
                "END_ITEM_NAME": _text(item, "END_ITEM_NAME"),
                "FSC": fsc,
                "FSG": fsg,
                "FSG_TITLE": fsg_title,
                "FSC_TITLE": fsc_title,
                "INC": inc,
                "INC_DEFINITION": inc_definition,
            }
        )

        if not fsc:
            unmatched.append(
                {"NIIN": niin, "code_type": "FSC", "code": fsc, "reason": "missing FSC on selected item"}
            )
        else:
            if fsc_row is None:
                unmatched.append(
                    {
                        "NIIN": niin,
                        "code_type": "FSC",
                        "code": fsc,
                        "reason": "FSC not found in V_H2_FSC.CSV",
                    }
                )
            if fsg_row is None:
                unmatched.append(
                    {
                        "NIIN": niin,
                        "code_type": "FSG",
                        "code": fsg,
                        "reason": "FSG title not found in V_H2_FSG.CSV for this FSC",
                    }
                )
        if not inc:
            unmatched.append(
                {"NIIN": niin, "code_type": "INC", "code": inc, "reason": "missing INC on selected item"}
            )
        elif inc_row is None:
            unmatched.append(
                {
                    "NIIN": niin,
                    "code_type": "INC",
                    "code": inc,
                    "reason": "INC not found in V_H6_NAME_INC.CSV",
                }
            )

    return classified, unmatched


def group_items(classified: list[dict[str, str]]) -> list[dict[str, str]]:
    counts: Counter[tuple[str, str, str, str, str]] = Counter()
    for row in classified:
        counts[
            (row["FSG"], row["FSG_TITLE"], row["FSC"], row["FSC_TITLE"], row["INC"])
        ] += 1
    groups = [
        {
            "FSG": fsg,
            "FSG_TITLE": fsg_title,
            "FSC": fsc,
            "FSC_TITLE": fsc_title,
            "INC": inc,
            "item_count": str(count),
        }
        for (fsg, fsg_title, fsc, fsc_title, inc), count in counts.items()
    ]
    groups.sort(key=lambda row: (-int(row["item_count"]), row["FSG"], row["FSC"], row["INC"]))
    return groups


def write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows(rows)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Priority 4: translate selected-item FSC/FSG/INC codes using H2/H6 lookups."
    )
    parser.add_argument("--items", type=Path, default=DEFAULT_ITEMS)
    parser.add_argument("--fsg", type=Path, default=DEFAULT_FSG)
    parser.add_argument("--fsc", type=Path, default=DEFAULT_FSC)
    parser.add_argument("--inc", type=Path, default=DEFAULT_INC)
    parser.add_argument("--classified-output", type=Path, default=DEFAULT_CLASSIFIED)
    parser.add_argument("--groups-output", type=Path, default=DEFAULT_GROUPS)
    parser.add_argument("--unmatched-output", type=Path, default=DEFAULT_UNMATCHED)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    missing = [
        path
        for label, path in (
            ("selected items", args.items),
            ("V_H2_FSG.CSV", args.fsg),
            ("V_H2_FSC.CSV", args.fsc),
            ("V_H6_NAME_INC.CSV", args.inc),
        )
        if not path.is_file()
    ]
    if missing:
        for path in missing:
            print(f"Input not found: {path}")
        print("Place H2/H6 lookups under data/raw/ and run Stage 3 first. Do not commit the lookup CSVs.")
        return 1

    with args.items.open(encoding="utf-8", newline="") as handle:
        items = [{name: (value or "").strip() for name, value in row.items()} for row in csv.DictReader(handle)]
    needed_incs = {_text(item, "INC") for item in items if _text(item, "INC")}

    fsg_lookup, fsg_rows = load_csv_by_key(args.fsg, "FSC")
    fsc_lookup, fsc_rows = load_csv_by_key(args.fsc, "FSC")
    inc_lookup, inc_rows = load_inc_lookups(args.inc, needed_incs)

    classified, unmatched = classify_items(items, fsg_lookup, fsc_lookup, inc_lookup)
    groups = group_items(classified)
    write_csv(args.classified_output, CLASSIFIED_FIELDS, classified)
    write_csv(args.groups_output, GROUP_FIELDS, groups)
    write_csv(args.unmatched_output, UNMATCHED_FIELDS, unmatched)

    fsc_unmatched = sum(1 for row in unmatched if row["code_type"] == "FSC")
    fsg_unmatched = sum(1 for row in unmatched if row["code_type"] == "FSG")
    inc_unmatched = sum(1 for row in unmatched if row["code_type"] == "INC")
    print(
        "Priority 4 complete. "
        f"fsg_lookup_rows={fsg_rows:,} "
        f"fsc_lookup_rows={fsc_rows:,} "
        f"inc_lookup_rows={inc_rows:,} "
        f"selected_items={len(items):,} "
        f"classified={len(classified):,} "
        f"groups={len(groups):,} "
        f"unmatched_fsc={fsc_unmatched:,} "
        f"unmatched_fsg={fsg_unmatched:,} "
        f"unmatched_inc={inc_unmatched:,}"
    )
    print(f"Classified: {args.classified_output}")
    print(f"Groups: {args.groups_output}")
    print(f"Unmatched: {args.unmatched_output}")
    print("Classification lookups describe item type, not material composition.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
