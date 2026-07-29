from __future__ import annotations

from datetime import date
from typing import Any


def _parse_iso_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value.strip()[:10])
    except (TypeError, ValueError):
        return None


def check_freshness(
    items: list[dict[str, Any]] | None = None,
    as_of: str = "",
    max_age_days: int = 365,
) -> dict[str, Any]:
    if not items:
        return {
            "tool": "freshness_check",
            "error": "missing_items",
            "message": "At least one dated item is required.",
            "items": [],
            "status_counts": {"fresh": 0, "stale": 0, "future": 0, "invalid": 0},
            "item_count": 0,
            "fresh_count": 0,
            "stale_count": 0,
        }

    reference_date = _parse_iso_date(as_of) if as_of else date.today()
    if reference_date is None:
        return {
            "tool": "freshness_check",
            "error": "invalid_as_of",
            "message": "as_of must use ISO YYYY-MM-DD.",
            "items": [],
            "status_counts": {"fresh": 0, "stale": 0, "future": 0, "invalid": 0},
            "item_count": len(items),
            "fresh_count": 0,
            "stale_count": 0,
        }
    if max_age_days < 0:
        return {
            "tool": "freshness_check",
            "error": "invalid_max_age_days",
            "message": "max_age_days must be zero or greater.",
            "items": [],
            "status_counts": {"fresh": 0, "stale": 0, "future": 0, "invalid": 0},
            "item_count": len(items),
            "fresh_count": 0,
            "stale_count": 0,
        }

    results: list[dict[str, Any]] = []
    status_counts = {"fresh": 0, "stale": 0, "future": 0, "invalid": 0}

    for index, item in enumerate(items):
        title = str(item.get("title") or f"Item {index + 1}").strip()
        raw_date = str(item.get("date") or "").strip()
        published_date = _parse_iso_date(raw_date)

        if published_date is None:
            status = "invalid"
            age_days = None
            recommendation = "Provide the item date as ISO YYYY-MM-DD."
        else:
            age_days = (reference_date - published_date).days
            if age_days < 0:
                status = "future"
                recommendation = "Review the date because it is later than the reference date."
            elif age_days <= max_age_days:
                status = "fresh"
                recommendation = "The item is within the requested freshness window."
            else:
                status = "stale"
                recommendation = "Find a newer source or explain why this older source remains relevant."

        status_counts[status] += 1
        results.append({
            "index": index,
            "title": title,
            "date": raw_date,
            "age_days": age_days,
            "status": status,
            "recommendation": recommendation,
        })

    return {
        "tool": "freshness_check",
        "error": None,
        "message": None,
        "as_of": reference_date.isoformat(),
        "max_age_days": max_age_days,
        "items": results,
        "status_counts": status_counts,
        "item_count": len(results),
        "fresh_count": status_counts["fresh"],
        "stale_count": status_counts["stale"],
    }

