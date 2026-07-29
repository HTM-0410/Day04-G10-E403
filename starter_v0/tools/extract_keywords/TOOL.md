---
name: extract_keywords
description: Extracts the most relevant keywords from a given text.
---

# extract_keywords

Use this tool when the user asks to find the most important topics, entities, or keywords in a piece of text.

## Inputs

- `text` (string): The raw text from which to extract keywords.
- `max_keywords` (integer, optional): The maximum number of keywords to return. Defaults to 5.

## Usage constraints

- Only use this if the user provides the text to be processed in their request.
