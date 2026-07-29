from __future__ import annotations

from typing import Any

def check_claim(claim: str) -> dict[str, Any]:
    if not claim or not claim.strip():
        return {
            "tool": "fact_check",
            "error": "missing_claim",
            "message": "The claim to check cannot be empty.",
            "verdict": None,
            "reasoning": None,
        }
    
    # Mock implementation of fact checking
    claim_lower = claim.lower()
    
    if "flat" in claim_lower and "earth" in claim_lower:
        verdict = "False"
        reasoning = "Scientific evidence overwhelmingly supports that the Earth is an oblate spheroid."
    elif "water" in claim_lower and ("boil" in claim_lower or "100" in claim_lower):
        verdict = "True"
        reasoning = "Water boils at 100 degrees Celsius at sea level (1 atm pressure)."
    elif "ai" in claim_lower and "dangerous" in claim_lower:
        verdict = "Mixed"
        reasoning = "AI poses potential risks and dangers, but also offers significant benefits. It is a topic of ongoing debate."
    else:
        verdict = "Unknown"
        reasoning = "I don't have enough information in my mock database to verify this specific claim."

    return {
        "tool": "fact_check",
        "error": None,
        "message": None,
        "claim": claim,
        "verdict": verdict,
        "reasoning": reasoning,
    }
