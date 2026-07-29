from __future__ import annotations

from typing import Any

from tools.source_triage.tool import triage_sources


def compare_sources(urls: list[str] | None = None, criteria: str = "general") -> dict[str, Any]:
    if not urls or len(urls) < 2:
        return {
            "tool": "source_compare",
            "error": "insufficient_urls",
            "message": "At least two URLs are required for comparison.",
            "items": [],
            "comparison": None,
        }

    triage_result = triage_sources(urls)

    items = triage_result.get("items", [])
    tier_counts = triage_result.get("tier_counts", {})

    item_summaries = []
    for item in items:
        item_summaries.append({
            "url": item.get("url"),
            "tier": item.get("tier"),
            "category": item.get("category"),
            "recommendation": item.get("recommendation"),
        })

    tiers_ranked = sorted(item_summaries, key=lambda x: x["tier"])

    comparison = {
        "criteria": criteria,
        "total_sources": len(items),
        "tier_distribution": tier_counts,
        "most_reliable": tiers_ranked[0] if tiers_ranked else None,
        "least_reliable": tiers_ranked[-1] if tiers_ranked else None,
        "summary": f"Compared {len(items)} sources. Most reliable: {tiers_ranked[0]['url'] if tiers_ranked else 'N/A'} (Tier {tiers_ranked[0]['tier'] if tiers_ranked else 'N/A'}).",
    }

    return {
        "tool": "source_compare",
        "error": None,
        "message": None,
        "items": item_summaries,
        "comparison": comparison,
    }
