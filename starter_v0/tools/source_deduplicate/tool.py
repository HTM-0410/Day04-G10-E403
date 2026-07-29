from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


TRACKING_PARAMETERS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "ref_src",
}


def _canonicalize_url(raw_url: str) -> tuple[str | None, str | None]:
    candidate = raw_url.strip()
    if not candidate:
        return None, "empty_url"
    if "://" not in candidate:
        candidate = f"https://{candidate}"

    parsed = urlparse(candidate)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower().removeprefix("www.")
    if scheme not in {"http", "https"} or not host:
        return None, "invalid_http_url"

    try:
        port = parsed.port
    except ValueError:
        return None, "invalid_port"
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        host = f"{host}:{port}"

    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")

    query_pairs = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in TRACKING_PARAMETERS
    ]
    query_pairs.sort()
    canonical = urlunparse((scheme, host, path, "", urlencode(query_pairs), ""))
    return canonical, None


def deduplicate_sources(urls: list[str] | None = None) -> dict[str, Any]:
    if not urls:
        return {
            "tool": "source_deduplicate",
            "error": "missing_urls",
            "message": "At least one URL is required.",
            "items": [],
            "unique_urls": [],
            "input_count": 0,
            "unique_count": 0,
            "duplicate_count": 0,
            "invalid_count": 0,
        }

    items: list[dict[str, Any]] = []
    unique_urls: list[str] = []
    first_index_by_url: dict[str, int] = {}
    duplicate_count = 0
    invalid_count = 0

    for index, raw_value in enumerate(urls):
        original = str(raw_value).strip()
        canonical, issue = _canonicalize_url(original)
        if issue:
            invalid_count += 1
            items.append({
                "index": index,
                "original_url": original,
                "canonical_url": None,
                "status": "invalid",
                "duplicate_of": None,
                "issue": issue,
            })
            continue

        duplicate_of = first_index_by_url.get(canonical)
        if duplicate_of is None:
            first_index_by_url[canonical] = index
            unique_urls.append(canonical)
            status = "unique"
        else:
            duplicate_count += 1
            status = "duplicate"

        items.append({
            "index": index,
            "original_url": original,
            "canonical_url": canonical,
            "status": status,
            "duplicate_of": duplicate_of,
            "issue": None,
        })

    return {
        "tool": "source_deduplicate",
        "error": None,
        "message": None,
        "items": items,
        "unique_urls": unique_urls,
        "input_count": len(urls),
        "unique_count": len(unique_urls),
        "duplicate_count": duplicate_count,
        "invalid_count": invalid_count,
    }
