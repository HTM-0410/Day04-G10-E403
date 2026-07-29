---
name: summarize_text
description: Provides a concise summary of a given block of text.
---

# summarize_text

Use this tool when the user explicitly asks to summarize a piece of text. 

## Inputs

- `text` (string): The raw text to summarize.

## Usage constraints

- Only use this if the user provides the text to be summarized in their request.
- If the user asks to summarize a URL, use `fetch` first, or ask for the URL if they didn't provide one. Do NOT use `summarize_text` with just a URL.
