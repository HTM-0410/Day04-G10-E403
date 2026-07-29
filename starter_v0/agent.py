from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from providers.base import Provider, ToolCall
from tools import TOOL_FUNCTIONS


BATCH_ARRAY_ARGUMENTS = {
    "source_triage": "urls",
    "source_deduplicate": "urls",
}


def coalesce_batch_tool_calls(calls: list[ToolCall]) -> list[ToolCall]:
    """Merge repeated calls for tools whose contract requires one array batch."""
    merged: list[ToolCall] = []
    batch_positions: dict[str, int] = {}

    for call in calls:
        array_arg = BATCH_ARRAY_ARGUMENTS.get(call.name)
        values = call.args.get(array_arg) if array_arg else None
        if not array_arg or not isinstance(values, list):
            merged.append(call)
            continue

        existing_position = batch_positions.get(call.name)
        if existing_position is None:
            copied_args = dict(call.args)
            copied_args[array_arg] = list(values)
            batch_positions[call.name] = len(merged)
            merged.append(ToolCall(name=call.name, args=copied_args))
            continue

        existing_values = merged[existing_position].args[array_arg]
        for value in values:
            if value not in existing_values:
                existing_values.append(value)

    return merged


@dataclass
class AgentRun:
    text: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)


class ResearchAgent:
    def __init__(
        self,
        provider: Provider,
        *,
        system_prompt: str,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> None:
        self.provider = provider
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.model = model

    def run(self, user_messages: list[dict[str, str]], *, tool_choice: Any | None = None) -> AgentRun:
        messages = [{"role": "system", "content": self.system_prompt}, *user_messages]
        response = self.provider.complete(
            messages,
            self.tools,
            model=self.model,
            temperature=0.0,
            tool_choice=tool_choice,
        )
        tool_calls = coalesce_batch_tool_calls(response.tool_calls)
        results: list[dict[str, Any]] = []
        for call in tool_calls:
            func = TOOL_FUNCTIONS.get(call.name)
            if not func:
                results.append({"tool": call.name, "error": "unknown_tool"})
                continue
            try:
                result = func(**call.args)
            except Exception as exc:  # keep eval robust; failures are evidence
                result = {"error": type(exc).__name__, "message": str(exc)}
            results.append({"tool": call.name, "args": call.args, "result": result})
        return AgentRun(text=response.text, tool_calls=tool_calls, tool_results=results)
