# Live replay artifacts

The Streamlit demo uses these files to replay prompt behavior by version.

- `v0/system_prompt.md` and `v0/tools.yaml` are restored exactly from the starter baseline.
- `v1/system_prompt.md` is a replay reconstruction based on the v1 reason and hypothesis in `artifacts/version_log.csv`.
- `v2/system_prompt.md` is a replay reconstruction based on the v2 reason and hypothesis in `artifacts/version_log.csv`.
- v1 and v2 intentionally reuse the baseline tool declarations because their historical `tools_hash` did not change.
- v3 uses the final `artifacts/system_prompt.md` and `artifacts/tools.yaml`.

Saved run JSON in the Version lab remains the authoritative historical evidence. Replayed live output can vary by model and is not claimed to reproduce the historical run byte-for-byte.
