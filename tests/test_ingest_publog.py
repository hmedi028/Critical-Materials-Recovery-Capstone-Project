
import contextlib
import csv
import io
import tempfile
import unittest
from pathlib import Path

from cmr.ingest_publog import (
    DEFAULT_LIMIT,
    extract_candidate_niins,
    main,
    parse_args,
)


class TestIngestPublogArgs(unittest.TestCase):
    def test_positive_limit_is_accepted(self):
        args = parse_args(["--limit", "5"])
        self.assertEqual(args.limit, 5)

    def test_default_limit_is_1000(self):
        args = parse_args([])
        self.assertEqual(args.limit, DEFAULT_LIMIT)

    def test_zero_limit_is_rejected(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            result = main(["--limit", "0"])
        self.assertEqual(result, 2)
        self.assertIn("--limit must be at least 1", output.getvalue())

    def test_negative_limit_is_rejected(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            result = main(["--limit", "-5"])
        self.assertEqual(result, 2)
        self.assertIn("--limit must be at least 1", output.getvalue())


class TestExtractCandidateNiins(unittest.TestCase):
    def write_source_csv(self, folder, rows):
        path = Path(folder) / "P_FLIS_NSN.CSV"
        fields = [
            "FSC",
            "NIIN",
            "ITEM_NAME",
            "INC",
            "END_ITEM_NAME",
            "CANCELLED_NIIN",
        ]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_filters_fscs_and_cancelled_rows(self):
        rows = [
            {"FSC": "5960", "NIIN": "000000001", "ITEM_NAME": "Allowed"},
            {"FSC": "1234", "NIIN": "000000002", "ITEM_NAME": "Wrong FSC"},
            {
                "FSC": "5998",
                "NIIN": "000000003",
                "ITEM_NAME": "Cancelled",
                "CANCELLED_NIIN": "999999999",
            },
            {"FSC": "2840", "NIIN": "000000004", "ITEM_NAME": "Also allowed"},
        ]
        with tempfile.TemporaryDirectory() as folder:
            source = self.write_source_csv(folder, rows)
            result = extract_candidate_niins(source)

        self.assertEqual([row["NIIN"] for row in result], ["000000001", "000000004"])

    def test_deduplicates_niins(self):
        rows = [
            {"FSC": "5960", "NIIN": "000000001", "ITEM_NAME": "First row"},
            {"FSC": "5960", "NIIN": "000000001", "ITEM_NAME": "Duplicate row"},
            {"FSC": "5998", "NIIN": "000000002", "ITEM_NAME": "Second NIIN"},
        ]
        with tempfile.TemporaryDirectory() as folder:
            source = self.write_source_csv(folder, rows)
            result = extract_candidate_niins(source)

        self.assertEqual([row["NIIN"] for row in result], ["000000001", "000000002"])

    def test_respects_limit(self):
        rows = [
            {"FSC": "5960", "NIIN": f"{number:09d}", "ITEM_NAME": f"Item {number}"}
            for number in range(1, 4)
        ]
        with tempfile.TemporaryDirectory() as folder:
            source = self.write_source_csv(folder, rows)
            result = extract_candidate_niins(source, limit=2)

        self.assertEqual(len(result), 2)
        self.assertEqual([row["NIIN"] for row in result], ["000000001", "000000002"])


if __name__ == "__main__":
    unittest.main()
