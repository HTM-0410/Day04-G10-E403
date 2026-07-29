from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import TOOL_FUNCTIONS  # noqa: E402
from agent import coalesce_batch_tool_calls  # noqa: E402
from providers.base import ToolCall  # noqa: E402


def main() -> None:
    deduplicate = TOOL_FUNCTIONS["source_deduplicate"](
        [
            "https://www.example.com/report?utm_source=demo",
            "https://example.com/report#summary",
            "https://example.org/data",
        ]
    )
    assert deduplicate["error"] is None
    assert deduplicate["unique_count"] == 2
    assert deduplicate["duplicate_count"] == 1

    freshness = TOOL_FUNCTIONS["freshness_check"](
        items=[
            {"title": "Recent report", "date": "2026-07-01"},
            {"title": "Old report", "date": "2024-01-01"},
        ],
        as_of="2026-07-29",
        max_age_days=90,
    )
    assert freshness["error"] is None
    assert freshness["status_counts"]["fresh"] == 1
    assert freshness["status_counts"]["stale"] == 1

    coverage = TOOL_FUNCTIONS["claim_coverage"](
        claims=[
            {"id": "C1", "text": "The system passed the eval."},
            {"id": "C2", "text": "The system has no provider errors."},
        ],
        evidence=[
            {"url": "https://example.com/run.json", "claim_ids": ["C1"]},
        ],
    )
    assert coverage["error"] is None
    assert coverage["coverage_rate"] == 0.5
    assert coverage["uncovered_claim_ids"] == ["C2"]

    batched_calls = coalesce_batch_tool_calls([
        ToolCall(name="source_triage", args={"urls": ["https://who.int/news"]}),
        ToolCall(name="source_triage", args={"urls": ["https://x.com/example/status/1"]}),
    ])
    assert len(batched_calls) == 1
    assert batched_calls[0].args["urls"] == [
        "https://who.int/news",
        "https://x.com/example/status/1",
    ]

    summary = {
        "source_deduplicate": {
            "error": deduplicate["error"],
            "unique_count": deduplicate["unique_count"],
            "duplicate_count": deduplicate["duplicate_count"],
        },
        "freshness_check": {
            "error": freshness["error"],
            "status_counts": freshness["status_counts"],
        },
        "claim_coverage": {
            "error": coverage["error"],
            "coverage_rate": coverage["coverage_rate"],
            "uncovered_claim_ids": coverage["uncovered_claim_ids"],
        },
        "batch_guard": {
            "call_count": len(batched_calls),
            "url_count": len(batched_calls[0].args["urls"]),
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
