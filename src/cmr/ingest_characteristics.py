"""Stage 2 PUB LOG characteristics scan.

Streams V_CHARACTERISTICS.CSV from CHARACTERISTICS.zip (or an extracted CSV)
without loading the 40-million-row file into memory. Candidate NIINs come from
Stage 1 (candidate_niins_nsn.csv). Matches are USGS 2025 names plus a few
aliases. Alloy/coating/plating are discovery flags, not a specific mineral.

Matches are candidate evidence, not a bill of materials.

Run:
    python -m cmr.ingest_characteristics
    python -m cmr.ingest_characteristics --input ~/Downloads/CHARACTERISTICS.zip
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
USGS_CSV = REPO_ROOT / "data" / "static" / "usgs" / "critical_minerals_2025.csv"

DEFAULT_CANDIDATES = PROCESSED_DIR / "candidate_niins_nsn.csv"
DEFAULT_EVIDENCE = PROCESSED_DIR / "selected_material_evidence.csv"
DEFAULT_SELECTED = PROCESSED_DIR / "selected_niins.csv"
DEFAULT_CHUNK_SIZE = 50_000

ZIP_MEMBER_HINT = "V_CHARACTERISTICS.CSV"
TEXT_FIELDS = ("NIIN", "MRC", "REQUIREMENTS_STATEMENT", "CLEAR_TEXT_REPLY")
EVIDENCE_FIELDS = (
    "NIIN",
    "MRC",
    "CRITICAL_MATERIAL",
    "MATCHED_TERM",
    "REQUIREMENTS_STATEMENT",
    "CLEAR_TEXT_REPLY",
)

ALIASES: tuple[tuple[str, str], ...] = (
    ("aluminium", "aluminum"),
    ("rare earth", "rare_earth_elements"),
    ("rare-earth", "rare_earth_elements"),
    ("rare earths", "rare_earth_elements"),
    ("rare-earths", "rare_earth_elements"),
    ("ree", "rare_earth_elements"),
)
DISCOVERY_TERMS = ("alloy", "coating", "plating")


@dataclass(frozen=True)
class MatchTerm:
    surface: str
    critical_material: str
    kind: str


def resolve_default_input() -> Path:
    downloads = Path.home() / "Downloads" / "CHARACTERISTICS.zip"
    if downloads.is_file():
        return downloads
    return RAW_DIR / "V_CHARACTERISTICS.CSV"


def load_candidate_niins(path: Path) -> set[str]:
    niins: set[str] = set()
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            niin = (row.get("NIIN") or "").strip()
            if niin:
                niins.add(niin)
    return niins


def load_match_terms(usgs_path: Path = USGS_CSV) -> list[MatchTerm]:
    terms: list[MatchTerm] = []
    with usgs_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            material_id = (row.get("material_id") or "").strip()
            name = (row.get("material_name") or "").strip()
            if material_id and name:
                terms.append(MatchTerm(name.lower(), material_id, "usgs"))
    for surface, material_id in ALIASES:
        terms.append(MatchTerm(surface, material_id, "alias"))
    for surface in DISCOVERY_TERMS:
        terms.append(MatchTerm(surface, "", "discovery"))
    terms.sort(key=lambda term: len(term.surface), reverse=True)
    return terms


def compile_term_pattern(terms: list[MatchTerm]) -> tuple[re.Pattern[str], dict[str, MatchTerm]]:
    by_surface = {term.surface: term for term in terms}
    pattern = re.compile(
        r"(?<![A-Za-z0-9])("
        + "|".join(re.escape(term.surface) for term in terms)
        + r")(?![A-Za-z0-9])",
        re.IGNORECASE,
    )
    return pattern, by_surface


def find_matches(text: str, pattern: re.Pattern[str], by_surface: dict[str, MatchTerm]) -> list[MatchTerm]:
    found: dict[str, MatchTerm] = {}
    for match in pattern.finditer(text):
        surface = match.group(1).lower()
        term = by_surface.get(surface)
        if term is not None:
            found[f"{term.kind}:{term.surface}"] = term
    return list(found.values())


def open_characteristics(path: Path) -> tuple[Iterator[dict[str, str]], list[object]]:
    closers: list[object] = []
    if path.suffix.lower() == ".zip":
        archive = zipfile.ZipFile(path)
        closers.append(archive)
        member = next(
            (name for name in archive.namelist() if name.upper().endswith(ZIP_MEMBER_HINT)),
            None,
        )
        if member is None:
            archive.close()
            raise FileNotFoundError(f"{path} does not contain {ZIP_MEMBER_HINT}")
        binary = archive.open(member)
        closers.append(binary)
        handle = io.TextIOWrapper(binary, encoding="utf-8", errors="replace", newline="")
        closers.append(handle)
        reader = csv.DictReader(handle)
        return reader, closers
    handle = path.open(encoding="utf-8", errors="replace", newline="")
    closers.append(handle)
    return csv.DictReader(handle), closers


def close_all(closers: list[object]) -> None:
    for item in reversed(closers):
        close = getattr(item, "close", None)
        if close is not None:
            close()


def row_text(row: dict[str, str | None]) -> str:
    return " ".join(
        (row.get(name) or "").strip()
        for name in ("REQUIREMENTS_STATEMENT", "CLEAR_TEXT_REPLY")
        if (row.get(name) or "").strip()
    )


def scan_characteristics(
    input_path: Path,
    candidates: set[str],
    terms: list[MatchTerm],
    evidence_path: Path,
    selected_path: Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> dict[str, int]:
    pattern, by_surface = compile_term_pattern(terms)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    selected_path.parent.mkdir(parents=True, exist_ok=True)

    reader, closers = open_characteristics(input_path)
    rows_read = 0
    match_rows = 0
    selected: set[str] = set()

    try:
        with evidence_path.open("w", encoding="utf-8", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=list(EVIDENCE_FIELDS))
            writer.writeheader()
            chunk: list[dict[str, str]] = []

            def flush() -> None:
                nonlocal match_rows
                for row in chunk:
                    niin = (row.get("NIIN") or "").strip()
                    if not niin or niin not in candidates:
                        continue
                    hits = find_matches(row_text(row), pattern, by_surface)
                    if not hits:
                        continue
                    for term in hits:
                        writer.writerow(
                            {
                                "NIIN": niin,
                                "MRC": (row.get("MRC") or "").strip(),
                                "CRITICAL_MATERIAL": term.critical_material,
                                "MATCHED_TERM": term.surface,
                                "REQUIREMENTS_STATEMENT": (row.get("REQUIREMENTS_STATEMENT") or "").strip(),
                                "CLEAR_TEXT_REPLY": (row.get("CLEAR_TEXT_REPLY") or "").strip(),
                            }
                        )
                        match_rows += 1
                        if term.kind != "discovery":
                            selected.add(niin)
                chunk.clear()
                out.flush()

            for raw in reader:
                rows_read += 1
                chunk.append({name: raw.get(name) or "" for name in TEXT_FIELDS})
                if len(chunk) >= chunk_size:
                    flush()
                    print(f"Read {rows_read:,} rows; {match_rows:,} evidence rows; {len(selected):,} selected NIINs")
            flush()
    finally:
        close_all(closers)

    with selected_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["NIIN"])
        writer.writeheader()
        for niin in sorted(selected):
            writer.writerow({"NIIN": niin})

    return {
        "rows_read": rows_read,
        "candidate_niins": len(candidates),
        "match_rows": match_rows,
        "selected_niins": len(selected),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage 2: stream V_CHARACTERISTICS and write USGS material evidence."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="CHARACTERISTICS.zip or V_CHARACTERISTICS.CSV",
    )
    parser.add_argument(
        "--candidates",
        type=Path,
        default=DEFAULT_CANDIDATES,
        help="Stage 1 candidate NIIN CSV (default: data/processed/candidate_niins_nsn.csv)",
    )
    parser.add_argument(
        "--evidence-output",
        type=Path,
        default=DEFAULT_EVIDENCE,
        help="Evidence CSV (default: data/processed/selected_material_evidence.csv)",
    )
    parser.add_argument(
        "--selected-output",
        type=Path,
        default=DEFAULT_SELECTED,
        help="Distinct selected NIINs (default: data/processed/selected_niins.csv)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"Rows per chunk (default: {DEFAULT_CHUNK_SIZE})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    input_path = args.input or resolve_default_input()
    if not input_path.is_file():
        print(
            f"Input not found: {input_path}\n"
            "Pass --input ~/Downloads/CHARACTERISTICS.zip or a local V_CHARACTERISTICS.CSV. "
            "Do not commit the 3 GB extract."
        )
        return 1
    if not args.candidates.is_file():
        print(
            f"Candidate list not found: {args.candidates}\n"
            "Run Stage 1 first: python -m cmr.ingest_publog"
        )
        return 1

    candidates = load_candidate_niins(args.candidates)
    terms = load_match_terms()
    stats = scan_characteristics(
        input_path,
        candidates,
        terms,
        args.evidence_output,
        args.selected_output,
        chunk_size=args.chunk_size,
    )
    print(
        "Stage 2 complete. "
        f"rows_read={stats['rows_read']:,} "
        f"candidate_niins={stats['candidate_niins']:,} "
        f"match_rows={stats['match_rows']:,} "
        f"selected_niins={stats['selected_niins']:,}"
    )
    print(f"Evidence: {args.evidence_output}")
    print(f"Selected NIINs: {args.selected_output}")
    print("Treat matches as candidate evidence, not a confirmed bill of materials.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
