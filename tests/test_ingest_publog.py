import contextlib
import io
import unittest

from cmr.ingest_publog import main, parse_args


class TestIngestPublogArgs(unittest.TestCase):
    def test_positive_limit_is_accepted(self):
        args = parse_args(["--limit", "5"])
        self.assertEqual(args.limit, 5)

    def test_default_limit_is_1000(self):
        args = parse_args([])
        self.assertEqual(args.limit, 1000)

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


if __name__ == "__main__":
    unittest.main()
