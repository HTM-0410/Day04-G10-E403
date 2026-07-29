---
name: source_deduplicate
track: bonus
kind: local_formatter
requires_env: []
inputs: [urls]
outputs: [items, unique_urls, duplicate_count, invalid_count, error]
side_effect: false
---
# source_deduplicate

Normalizes a user-provided list of source URLs and removes duplicates caused by
fragments, common tracking parameters, `www`, default ports, or a trailing slash.

Use this tool only when the user already supplied URLs and explicitly asks to
deduplicate, clean, normalize, or consolidate them. It does not fetch pages,
check whether a URL is reachable, assess credibility, or verify claims.

