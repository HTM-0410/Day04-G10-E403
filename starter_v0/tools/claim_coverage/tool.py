from __future__ import annotations

from typing import Any


def audit_claim_coverage(
    claims: list[dict[str, Any]] | None = None,
    evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if not claims:
        return {
            "tool": "claim_coverage",
            "error": "missing_claims",
            "message": "At least one claim is required.",
            "claims": [],
            "uncovered_claim_ids": [],
            "unknown_claim_ids": [],
            "claim_count": 0,
            "covered_count": 0,
            "coverage_rate": 0.0,
        }
    if evidence is None:
        return {
            "tool": "claim_coverage",
            "error": "missing_evidence",
            "message": "An evidence list is required; use an empty list when no evidence exists.",
            "claims": [],
            "uncovered_claim_ids": [],
            "unknown_claim_ids": [],
            "claim_count": len(claims),
            "covered_count": 0,
            "coverage_rate": 0.0,
        }

    normalized_claims: list[dict[str, str]] = []
    claim_urls: dict[str, list[str]] = {}
    duplicate_claim_ids: list[str] = []

    for index, item in enumerate(claims):
        claim_id = str(item.get("id") or f"C{index + 1}").strip()
        text = str(item.get("text") or "").strip()
        if claim_id in claim_urls:
            duplicate_claim_ids.append(claim_id)
            continue
        normalized_claims.append({"id": claim_id, "text": text})
        claim_urls[claim_id] = []

    unknown_claim_ids: set[str] = set()
    invalid_evidence_count = 0
    for item in evidence:
        url = str(item.get("url") or "").strip()
        claim_ids = item.get("claim_ids") or []
        if not url or not isinstance(claim_ids, list):
            invalid_evidence_count += 1
            continue
        for raw_claim_id in claim_ids:
            claim_id = str(raw_claim_id).strip()
            if claim_id not in claim_urls:
                unknown_claim_ids.add(claim_id)
                continue
            if url not in claim_urls[claim_id]:
                claim_urls[claim_id].append(url)

    results: list[dict[str, Any]] = []
    uncovered_claim_ids: list[str] = []
    for claim in normalized_claims:
        urls = claim_urls[claim["id"]]
        covered = bool(urls)
        if not covered:
            uncovered_claim_ids.append(claim["id"])
        results.append({
            **claim,
            "covered": covered,
            "source_count": len(urls),
            "urls": urls,
        })

    claim_count = len(results)
    covered_count = claim_count - len(uncovered_claim_ids)
    coverage_rate = round(covered_count / claim_count, 4) if claim_count else 0.0

    return {
        "tool": "claim_coverage",
        "error": None,
        "message": None,
        "claims": results,
        "uncovered_claim_ids": uncovered_claim_ids,
        "unknown_claim_ids": sorted(unknown_claim_ids),
        "duplicate_claim_ids": duplicate_claim_ids,
        "invalid_evidence_count": invalid_evidence_count,
        "claim_count": claim_count,
        "covered_count": covered_count,
        "coverage_rate": coverage_rate,
    }

