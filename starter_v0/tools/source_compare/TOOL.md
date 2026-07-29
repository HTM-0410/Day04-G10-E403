---
name: source_compare
track: core
kind: local_formatter
requires_env: []
inputs: [urls, criteria]
outputs: [items, comparison, error]
side_effect: false
---
# source_compare

Compares multiple source URLs side-by-side for credibility, bias, or coverage differences.

This tool uses source_triage internally to classify each URL, then provides a comparative analysis based on the specified criteria.

Use when the user explicitly asks to:
- Compare sources, websites, or URLs
- Check differences between multiple sources
- Evaluate which source is more reliable or authoritative

