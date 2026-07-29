from __future__ import annotations

from typing import Any

def summarize(text: str) -> dict[str, Any]:
    if not text or not text.strip():
        return {
            "tool": "summarize_text",
            "error": "missing_text",
            "message": "Text to summarize cannot be empty.",
            "summary": None,
        }
    
    # Mock implementation of summarization logic
    text = text.strip()
    words = text.split()
    if len(words) < 10:
        summary = text # Too short to summarize, return as is
    else:
        # A simple simulated summary for the lab
        summary = f"Summary: This text discusses {words[0]} and {words[-1]} in about {len(words)} words."

    return {
        "tool": "summarize_text",
        "error": None,
        "message": None,
        "summary": summary,
        "original_length": len(words),
    }
