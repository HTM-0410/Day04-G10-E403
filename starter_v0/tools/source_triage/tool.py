from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


TIER_1_HOSTS = {
    "arxiv.org",
    "docs.python.org",
    "developer.mozilla.org",
    "openai.com",
    "who.int",
    "worldbank.org",
}

TIER_2_HOSTS = {
    "apnews.com",
    "bbc.com",
    "bbc.co.uk",
    "reuters.com",
    "theguardian.com",
}

TIER_3_HOSTS = {
    "facebook.com",
    "news.ycombinator.com",
    "reddit.com",
    "tiktok.com",
    "x.com",
    "twitter.com",
}


def _normalized_host(url: str) -> str:
    candidate = url.strip()
    if "://" not in candidate:
        candidate = f"https://{candidate}"
    host = (urlparse(candidate).hostname or "").lower()
    return host.removeprefix("www.")


def _is_host_or_subdomain(host: str, candidates: set[str]) -> bool:
    return any(host == item or host.endswith(f".{item}") for item in candidates)


def _classify(host: str) -> tuple[int, str, str]:
    if not host:
        return 3, "invalid_or_missing_host", "Provide a valid source URL."
    if (
        host.endswith(".gov")
        or host.endswith(".gov.vn")
        or host.endswith(".edu")
        or _is_host_or_subdomain(host, TIER_1_HOSTS)
    ):
        return 1, "primary_or_authoritative", "Prefer this source for factual claims."
    if _is_host_or_subdomain(host, TIER_3_HOSTS):
        return 3, "social_or_community_signal", "Treat as a signal; verify with Tier 1 or Tier 2 evidence."
    if _is_host_or_subdomain(host, TIER_2_HOSTS):
        return 2, "established_reporting", "Check whether the report links to primary evidence."
    return 2, "unclassified_web_source", "Review authorship, evidence, date, and primary citations."


def triage_sources(urls: list[str] | None = None) -> dict[str, Any]:
    if not urls:
        return {
            "tool": "source_triage",
            "error": "missing_urls",
            "message": "At least one URL is required.",
            "items": [],
            "tier_counts": {"1": 0, "2": 0, "3": 0},
            "item_count": 0,
        }

    items: list[dict[str, Any]] = []
    tier_counts = {"1": 0, "2": 0, "3": 0}
    for raw_url in urls:
        url = str(raw_url).strip()
        host = _normalized_host(url)
        tier, category, recommendation = _classify(host)
        tier_counts[str(tier)] += 1
        items.append({
            "url": url,
            "host": host,
            "tier": tier,
            "category": category,
            "recommendation": recommendation,
        })

    return {
        "tool": "source_triage",
        "error": None,
        "message": None,
        "items": items,
        "tier_counts": tier_counts,
        "item_count": len(items),
    }

