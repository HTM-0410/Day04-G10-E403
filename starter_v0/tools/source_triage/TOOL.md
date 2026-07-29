---
name: source_triage
track: core
kind: local_formatter
requires_env: []
inputs: [urls]
outputs: [items, tier_counts, item_count, error]
side_effect: false
---
# source_triage

Classifies already-known source URLs into a simple research-evidence tier:

- Tier 1: primary or authoritative sources such as government, education, arXiv,
  official documentation, standards, and company-owned domains.
- Tier 2: established reporting and general web sources that should be checked
  against primary evidence.
- Tier 3: social networks, forums, and community posts that are signals only.

Use this tool only when the user supplies one or more URLs and asks to assess,
triage, rank, or check source credibility. It does not fetch pages, verify claims,
or replace `fetch`/`lookup`.

