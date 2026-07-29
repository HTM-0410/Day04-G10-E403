from __future__ import annotations

import json
import os
from datetime import datetime

import streamlit as st

from chat import (
    ARTIFACTS_DIR,
    ROOT,
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

load_lab_env(ROOT)

# Same agent loop, prompt, and tool declarations as chat.py / eval — no drift between UI and eval.
SYSTEM_PROMPT_PATH = ARTIFACTS_DIR / "system_prompt.md"
TOOLS_PATH = ARTIFACTS_DIR / "tools.yaml"
TRANSCRIPTS_DIR = ROOT / "transcripts"

PROVIDERS = ["openrouter", "openai", "anthropic", "gemini"]
SECRET_ENV_VARS = [
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY",
    "TAVILY_API_KEY", "FIRECRAWL_API_KEY", "RAPIDAPI_KEY",
    "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
]


def redact_secrets(value):
    """Recursively replace any known secret env var value with a placeholder before display/logging."""
    secrets = {os.getenv(name) for name in SECRET_ENV_VARS if os.getenv(name)}
    if not secrets:
        return value
    text = json.dumps(value, ensure_ascii=False, default=str)
    for secret in secrets:
        text = text.replace(secret, "***REDACTED***")
    return json.loads(text)


st.set_page_config(page_title="Research Agent", layout="wide")

with st.sidebar:
    st.header("Cấu hình")
    provider_name = st.selectbox("Provider", PROVIDERS, index=0)
    model_override = st.text_input("Model override (để trống = mặc định)", "")
    version_label = st.text_input("Artifact version label", "v0")
    history_window = st.number_input("History window (turns)", min_value=0, max_value=20, value=5)
    max_tool_rounds = st.number_input("Max tool rounds", min_value=1, max_value=10, value=4)
    if st.button("Reset hội thoại"):
        st.session_state.clear()
        st.rerun()


@st.cache_resource(show_spinner=False)
def get_provider(name: str):
    return make_provider(name)


system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
tool_declarations = load_tool_declarations(TOOLS_PATH)
openai_tools = to_openai_tools(tool_declarations)
artifact_version = build_artifact_version(version_label, SYSTEM_PROMPT_PATH, TOOLS_PATH)

try:
    provider = get_provider(provider_name)
except Exception as exc:
    st.error(f"Không khởi tạo được provider `{provider_name}`: {exc}")
    st.stop()

selected_model = model_override.strip() or getattr(provider, "default_model", None)

st.title("Research Agent")
st.caption(
    f"artifact_version = `{artifact_version.artifact_version}` · "
    f"provider = `{provider_name}` · model = `{selected_model}`"
)

if "history" not in st.session_state:
    st.session_state.history = []
if "turns" not in st.session_state:
    st.session_state.turns = []
if "transcript_path" not in st.session_state:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(version_label), safe_slug(provider_name), timestamp])
    st.session_state.transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    st.session_state.transcript_id = transcript_id


def render_rounds(rounds: list[dict]) -> None:
    for round_record in rounds:
        for call, event in zip(round_record.get("tool_calls", []), round_record.get("tool_results", [])):
            safe_args = redact_secrets(call["args"])
            safe_result = redact_secrets(event.get("result", {}))
            error = safe_result.get("error") if isinstance(safe_result, dict) else None
            label = f"Round {round_record['round']} · 🔧 {call['name']}({json.dumps(safe_args, ensure_ascii=False)})"
            with st.expander(label):
                st.write(f"**error:** {error}")
                st.json(safe_result)


for turn in st.session_state.turns:
    with st.chat_message("user"):
        st.write(turn["user"])
    with st.chat_message("assistant"):
        render_rounds(turn.get("rounds", []))
        st.write(turn.get("assistant_text") or "")
        st.caption(f"status: {turn.get('status')}")

user_text = st.chat_input("Nhập câu hỏi cho agent...")
if user_text:
    with st.chat_message("user"):
        st.write(user_text)

    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state.history, int(history_window)),
        {"role": "user", "content": user_text},
    ]

    turn_record: dict = {
        "turn_index": len(st.session_state.turns) + 1,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    with st.chat_message("assistant"):
        with st.spinner("Agent đang xử lý..."):
            try:
                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=openai_tools,
                    model=model_override.strip() or None,
                    max_tool_rounds=int(max_tool_rounds),
                )
                turn_record.update(result)
                assistant_text = result["assistant_text"]
                st.session_state.history.append({"role": "user", "content": user_text})
                st.session_state.history.append({"role": "assistant", "content": assistant_text})
            except Exception as exc:
                assistant_text = f"Lỗi provider: {type(exc).__name__}: {exc}"
                turn_record.update({
                    "status": "provider_error",
                    "assistant_text": assistant_text,
                    "error": f"{type(exc).__name__}: {exc}",
                })

        render_rounds(turn_record.get("rounds", []))
        st.write(assistant_text)
        st.caption(f"status: {turn_record.get('status')}")

    turn_record["ended_at"] = now_iso()
    st.session_state.turns.append(turn_record)

    transcript = {
        "transcript_id": st.session_state.transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "model": selected_model,
        "system_prompt": str(SYSTEM_PROMPT_PATH),
        "tools": str(TOOLS_PATH),
        "history_window": int(history_window),
        "max_tool_rounds": int(max_tool_rounds),
        "created_at": st.session_state.turns[0]["started_at"],
        "turns": redact_secrets(st.session_state.turns),
    }
    write_transcript(st.session_state.transcript_path, transcript)
    st.caption(f"Transcript: `{st.session_state.transcript_path}`")
