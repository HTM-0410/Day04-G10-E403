---
name: claim_coverage
track: bonus
kind: local_formatter
requires_env: []
inputs: [claims, evidence]
outputs: [claims, uncovered_claim_ids, unknown_claim_ids, coverage_rate, error]
side_effect: false
---
# claim_coverage

Audits whether each explicitly listed claim has at least one supplied evidence
URL. Evidence entries connect URLs to claims through `claim_ids`.

Use this tool only when the user supplies both a claim list and evidence-to-claim
mappings and asks for coverage, unsupported-claim, or evidence-gap analysis. It
does not fetch sources, verify claims, or decide whether evidence is credible.

