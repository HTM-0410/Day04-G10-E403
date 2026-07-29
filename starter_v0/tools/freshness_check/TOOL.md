---
name: freshness_check
track: bonus
kind: local_formatter
requires_env: []
inputs: [items, as_of, max_age_days]
outputs: [items, status_counts, fresh_count, stale_count, error]
side_effect: false
---
# freshness_check

Checks whether already-known research items are fresh or stale relative to an
explicit reference date and maximum age in days.

Use this tool only when the user supplies publication/update dates and asks for
a freshness, recency, or staleness audit. Dates should use ISO `YYYY-MM-DD`.
It does not search for dates, fetch pages, or judge factual accuracy.

