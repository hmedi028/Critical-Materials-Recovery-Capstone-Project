"""Stage 1 PUB LOG / FLIS NSN candidate slice.

Streams P_FLIS_NSN.CSV without loading the full file into memory.
The teammate's bulk extract stays local under data/raw/; output goes to
data/processed/. Neither file should be committed.

Run:
    python -m cmr.ingest_publog
    python -m cmr.ingest_publog --input /path/to/P_FLIS_NSN.CSV --limit 1000
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = REPO_ROOT / "data" / "raw" / "P_FLIS_NSN.CSV"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "processed" / "candidate_niins.csv"

TARGET_FSCS = {"5960", "5998", "6140", "2840"}
DEFAULT_LIMIT = 1000
OUTPUT_FIELDS = ("FSC", "NIIN", "ITEM_NAME", "INC", "END_ITEM_NAME")


def _text(row: dict[str, str], *names: str) -> str:
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def is_cancelled(row: dict[str, str]) -> bool:
    return bool(
        _text(
            row,
            "CANCELLED_NIIN",
            "CANCELLED_ITEM_NIIN",
            "CANCELLATION_NIIN",
        )
    )


def extract_candidate_niins(
    input_path: Path,
    limit: int = DEFAULT_LIMIT,
    target_fscs: set[str] | None = None,
) -> list[dict[str, str]]:
    """Stream the NSN file and return distinct NIIN rows for the target FSCs."""
    fscs = target_fscs or TARGET_FSCS
    seen_niins: set[str] = set()
    candidates: list[dict[str, str]] = []

    with input_path.open(mode="r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if is_cancelled(row):
                continue
            fsc = _text(row, "FSC")
            niin = _text(row, "NIIN")
            if not fsc or not niin or fsc not in fscs or niin in seen_niins:
                continue
            seen_niins.add(niin)
            candidates.append(
                {
                    "FSC": fsc,
                    "NIIN": niin,
                    "ITEM_NAME": _text(row, "ITEM_NAME"),
                    "INC": _text(row, "INC"),
                    "END_ITEM_NAME": _text(row, "END_ITEM_NAME"),
                }
            )
            if len(candidates) >= limit:
                break
    return candidates


def write_candidate_niins(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open(mode="w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(OUTPUT_FIELDS))
        writer.writeheader()
        writer.writerows(rows)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Slice a local P_FLIS_NSN.CSV into a candidate NIIN list."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to P_FLIS_NSN.CSV (default: data/raw/P_FLIS_NSN.CSV)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output CSV path (default: data/processed/candidate_niins.csv)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Maximum distinct NIINs to keep (default: {DEFAULT_LIMIT})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.input.is_file():
        print(
            f"Input not found: {args.input}\n"
            "Extract P_FLIS_NSN.CSV locally under data/raw/ or pass --input. "
            "Do not commit the bulk file."
        )
        return 1
    rows = extract_candidate_niins(args.input, limit=args.limit)
    write_candidate_niins(args.output, rows)
    print(f"Wrote {len(rows)} distinct candidate NIINs to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
