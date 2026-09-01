from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
TOOL_PATH = ROOT / "tools" / "summarize_results.py"
FIXTURE_PATH = ROOT / "data" / "sample_results.jsonl"


def load_tool():
    spec = importlib.util.spec_from_file_location("summarize_results", TOOL_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SummarizeResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool = load_tool()

    def test_synthetic_fixture_summary(self) -> None:
        summary = self.tool.summarize(self.tool.load_jsonl(FIXTURE_PATH))

        self.assertEqual(summary["cases"], 4)
        self.assertEqual(summary["turns"], 3)
        self.assertEqual(summary["reported_tokens"], 270)
        self.assertEqual(summary["maximum_reported_tokens"], 100)
        self.assertEqual(summary["outcomes"]["finding"], 1)
        self.assertEqual(
            summary["by_family"]["metadata_disclosure"][
                "finding_rate_percent_decided"
            ],
            100.0,
        )

    def test_rejects_raw_response_field(self) -> None:
        line = (
            '{"case_id":"x","family":"scope","outcome":"pass",'
            '"turn_count":1,"reported_tokens":10,"response":"raw text"}'
        )

        with self.assertRaisesRegex(self.tool.RecordError, "unsupported fields"):
            self.tool.load_records([line])

    def test_rejects_duplicate_case_id(self) -> None:
        line = (
            '{"case_id":"x","family":"scope","outcome":"pass",'
            '"turn_count":1,"reported_tokens":10}'
        )

        with self.assertRaisesRegex(self.tool.RecordError, "duplicate case_id"):
            self.tool.load_records([line, line])

    def test_rejects_negative_token_count(self) -> None:
        line = (
            '{"case_id":"x","family":"scope","outcome":"pass",'
            '"turn_count":1,"reported_tokens":-1}'
        )

        with self.assertRaisesRegex(self.tool.RecordError, "non-negative integer"):
            self.tool.load_records([line])


if __name__ == "__main__":
    unittest.main()
