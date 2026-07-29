from __future__ import annotations

from typing import Any
import re

def extract(text: str, max_keywords: int = 5) -> dict[str, Any]:
    if not text or not text.strip():
        return {
            "tool": "extract_keywords",
            "error": "missing_text",
            "message": "Text to extract keywords from cannot be empty.",
            "keywords": [],
        }
    
    # Mock implementation of keyword extraction
    # Strip non-alphanumeric and split
    words = re.sub(r'[^a-zA-Z0-9\s]', '', text.lower()).split()
    
    # Filter out common short words (stop words mock)
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "this", "that"}
    filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
    
    # Count frequencies
    freq = {}
    for w in filtered_words:
        freq[w] = freq.get(w, 0) + 1
        
    # Sort by frequency, then alphabetically
    sorted_keywords = sorted(freq.keys(), key=lambda k: (-freq[k], k))
    
    # Take top N
    top_keywords = sorted_keywords[:max_keywords]

    return {
        "tool": "extract_keywords",
        "error": None,
        "message": None,
        "keywords": top_keywords,
        "max_requested": max_keywords,
    }
