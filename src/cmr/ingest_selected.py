"""Stage 3 PUB LOG selected extracts.

Filters P_FLIS_NSN.CSV and V_FLIS_IDENTIFICATION.CSV to the Stage 2
selected_niins set. Builds the 13-digit NSN only after the item join.
Identification codes are supporting clues, not proof of a USGS material.

Run:
    python -m cmr.ingest_selected
    python -m cmr.ingest_selected --items data/raw/P_FLIS_NSN.CSV --identification ~/Downloads/IDENTIFICATION.zip
"""

from __future__ import annotations

import argparse
import csv
import io
import zipfile
from collections.abc import Iterator
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

DEFAULT_SELECTED = PROCESSED_DIR / "selected_niins.csv"
DEFAULT_ITEMS = RAW_DIR / "P_FLIS_NSN.CSV"
DEFAULT_ITEMS_OUTPUT = PROCESSED_DIR / "selected_items.csv"
DEFAULT_IDENTIFICATION_OUTPUT = PROCESSED_DIR / "selected_identification.csv"
IDENT_ZIP_MEMBER = "V_FLIS_IDENTIFICATION.CSV"
PROGRESS_EVERY = 500_000

ITEM_FIELDS = ("FSC", "NIIN", "NSN", "INC", "ITEM_NAME", "END_ITEM_NAME")
IDENTIFICATION_FIELDS = (
    "NIIN",
    "INC",
    "CRIT_CD",
    "PMIC",
    "DMIL",
    "HMIC",
    "HCC",
    "ENAC",
    "ESD_EMI",
    "DMIL_INT_CD",
)


def resolve_default_identification() -> Path:
    downloads = Path.home() / "Downloads"
    for name in ("IDENTIFICATION.zip", "Identification.zip"):
        candidate = downloads / name
        if candidate.is_file():
            return candidate
    return RAW_DIR / "V_FLIS_IDENTIFICATION.CSV"


def load_selected_niins(path: Path) -> set[str]:
    niins: set[str] = set()
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            niin = (row.get("NIIN") or "").strip()
            if niin:
                niins.add(niin)
    return niins


def _text(row: dict[str, str | None], *names: str) -> str:
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def compile_nsn(fsc: str, niin: str) -> str:
    return f"{fsc}{niin}"


def open_csv_or_zip(path: Path, member_hint: str) -> tuple[Iterator[dict[str, str]], list[object]]:
    closers: list[object] = []
    if path.suffix.lower() == ".zip":
        archive = zipfile.ZipFile(path)
        closers.append(archive)
        member = next(
            (name for name in archive.namelist() if name.upper().endswith(member_hint.upper())),
            None,
        )
        if member is None:
            archive.close()
            raise FileNotFoundError(f"{path} does not contain {member_hint}")
        binary = archive.open(member)
        closers.append(binary)
        handle = io.TextIOWrapper(binary, encoding="utf-8", errors="replace", newline="")
        closers.append(handle)
        return csv.DictReader(handle), closers
    handle = path.open(encoding="utf-8", errors="replace", newline="")
    closers.append(handle)
    return csv.DictReader(handle), closers


def close_all(closers: list[object]) -> None:
    for item in reversed(closers):
        close = getattr(item, "close", None)
        if close is not None:
            close()


def filter_items(input_path: Path, selected: set[str], output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    rows_read = 0
    reader, closers = open_csv_or_zip(input_path, "P_FLIS_NSN.CSV")
    try:
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(ITEM_FIELDS))
            writer.writeheader()
            for raw in reader:
                rows_read += 1
                niin = _text(raw, "NIIN")
                if niin in selected:
                    fsc = _text(raw, "FSC")
                    writer.writerow(
                        {
                            "FSC": fsc,
                            "NIIN": niin,
                            "NSN": compile_nsn(fsc, niin),
                            "INC": _text(raw, "INC"),
                            "ITEM_NAME": _text(raw, "ITEM_NAME"),
                            "END_ITEM_NAME": _text(raw, "END_ITEM_NAME"),
                        }
                    )
                    written += 1
                if rows_read % PROGRESS_EVERY == 0:
                    print(f"P_FLIS_NSN read {rows_read:,} rows; {written:,} selected items")
    finally:
        close_all(closers)
    return written


def filter_identification(input_path: Path, selected: set[str], output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    rows_read = 0
    reader, closers = open_csv_or_zip(input_path, IDENT_ZIP_MEMBER)
    try:
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(IDENTIFICATION_FIELDS))
            writer.writeheader()
            for raw in reader:
                rows_read += 1
                niin = _text(raw, "NIIN")
                if niin in selected:
                    writer.writerow({name: _text(raw, name) for name in IDENTIFICATION_FIELDS})
                    written += 1
                if rows_read % PROGRESS_EVERY == 0:
                    print(
                        f"V_FLIS_IDENTIFICATION read {rows_read:,} rows; "
                        f"{written:,} selected identification rows"
                    )
    finally:
        close_all(closers)
    return written


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage 3: write selected_items and selected_identification from selected NIINs."
    )
    parser.add_argument(
        "--selected",
        type=Path,
        default=DEFAULT_SELECTED,
        help="Stage 2 selected NIIN CSV (default: data/processed/selected_niins.csv)",
    )
    parser.add_argument(
        "--items",
        type=Path,
        default=DEFAULT_ITEMS,
        help="P_FLIS_NSN.CSV (default: data/raw/P_FLIS_NSN.CSV)",
    )
    parser.add_argument(
        "--identification",
        type=Path,
        default=None,
        help="Identification.zip or V_FLIS_IDENTIFICATION.CSV",
    )
    parser.add_argument(
        "--items-output",
        type=Path,
        default=DEFAULT_ITEMS_OUTPUT,
        help="Item extract (default: data/processed/selected_items.csv)",
    )
    parser.add_argument(
        "--identification-output",
        type=Path,
        default=DEFAULT_IDENTIFICATION_OUTPUT,
        help="Identification extract (default: data/processed/selected_identification.csv)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.selected.is_file():
        print(
            f"Selected NIIN list not found: {args.selected}\n"
            "Run Stage 2 first: python -m cmr.ingest_characteristics"
        )
        return 1
    if not args.items.is_file():
        print(
            f"Items input not found: {args.items}\n"
            "Extract P_FLIS_NSN.CSV under data/raw/ or pass --items. Do not commit the bulk file."
        )
        return 1

    selected = load_selected_niins(args.selected)
    item_rows = filter_items(args.items, selected, args.items_output)
    print(f"Wrote {item_rows:,} selected items to {args.items_output}")

    identification_path = args.identification or resolve_default_identification()
    if not identification_path.is_file():
        print(
            f"Identification input not found: {identification_path}\n"
            "Pass --identification ~/Downloads/Identification.zip or a local "
            "V_FLIS_IDENTIFICATION.CSV. Do not commit the 16M-row extract."
        )
        return 1

    identification_rows = filter_identification(
        identification_path, selected, args.identification_output
    )
    print(
        "Stage 3 complete. "
        f"selected_niins={len(selected):,} "
        f"selected_items={item_rows:,} "
        f"selected_identification={identification_rows:,}"
    )
    print(f"Items: {args.items_output}")
    print(f"Identification: {args.identification_output}")
    print("CRIT_CD, PMIC, DMIL, HMIC, and HCC are supporting codes, not material proof.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
