#!/usr/bin/env python3
"""Aggregate sanitized red-team result records without raw interaction data."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ALLOWED_FIELDS = {
    "case_id",
    "family",
    "outcome",
    "turn_count",
    "reported_tokens",
}
ALLOWED_OUTCOMES = {"pass", "finding", "inconclusive", "error"}


class RecordError(ValueError):
    """Raised when a result record violates the content-free schema."""


def _nonempty_string(record: dict[str, Any], field: str, line_number: int) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise RecordError(f"line {line_number}: {field} must be a non-empty string")
    return value.strip()


def _nonnegative_int(record: dict[str, Any], field: str, line_number: int) -> int:
    value = record.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RecordError(f"line {line_number}: {field} must be a non-negative integer")
    return value


def load_records(lines: Iterable[str]) -> list[dict[str, Any]]:
    """Parse and validate content-free JSONL records."""

    records: list[dict[str, Any]] = []
    seen_case_ids: set[str] = set()

    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RecordError(
                f"line {line_number}: invalid JSON ({exc.msg})"
            ) from exc
        if not isinstance(value, dict):
            raise RecordError(f"line {line_number}: record must be a JSON object")

        unexpected = sorted(set(value) - ALLOWED_FIELDS)
        if unexpected:
            raise RecordError(
                f"line {line_number}: unsupported fields: {', '.join(unexpected)}"
            )

        case_id = _nonempty_string(value, "case_id", line_number)
        if case_id in seen_case_ids:
            raise RecordError(f"line {line_number}: duplicate case_id {case_id!r}")
        seen_case_ids.add(case_id)

        family = _nonempty_string(value, "family", line_number)
        outcome = _nonempty_string(value, "outcome", line_number)
        if outcome not in ALLOWED_OUTCOMES:
            allowed = ", ".join(sorted(ALLOWED_OUTCOMES))
            raise RecordError(
                f"line {line_number}: outcome must be one of {allowed}"
            )

        records.append(
            {
                "case_id": case_id,
                "family": family,
                "outcome": outcome,
                "turn_count": _nonnegative_int(value, "turn_count", line_number),
                "reported_tokens": _nonnegative_int(
                    value, "reported_tokens", line_number
                ),
            }
        )

    return records


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return load_records(path.read_text(encoding="utf-8").splitlines())


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Return deterministic overall and per-family aggregates."""

    outcomes = Counter(record["outcome"] for record in records)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record["family"]].append(record)

    by_family: dict[str, dict[str, int | float]] = {}
    for family, family_records in sorted(grouped.items()):
        family_outcomes = Counter(record["outcome"] for record in family_records)
        decided = family_outcomes["pass"] + family_outcomes["finding"]
        finding_rate = (
            round(100 * family_outcomes["finding"] / decided, 1) if decided else 0.0
        )
        by_family[family] = {
            "cases": len(family_records),
            "pass": family_outcomes["pass"],
            "finding": family_outcomes["finding"],
            "inconclusive": family_outcomes["inconclusive"],
            "error": family_outcomes["error"],
            "finding_rate_percent_decided": finding_rate,
        }

    token_values = [record["reported_tokens"] for record in records]
    return {
        "schema_version": 1,
        "cases": len(records),
        "turns": sum(record["turn_count"] for record in records),
        "reported_tokens": sum(token_values),
        "maximum_reported_tokens": max(token_values, default=0),
        "outcomes": {
            outcome: outcomes[outcome] for outcome in sorted(ALLOWED_OUTCOMES)
        },
        "by_family": by_family,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Sanitized JSONL result file")
    parser.add_argument("--pretty", action="store_true", help="Indent JSON output")
    args = parser.parse_args()

    result = summarize(load_jsonl(args.path))
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))


if __name__ == "__main__":
    main()
