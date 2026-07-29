"""
Day 04 Research Agent — Streamlit UI
Reuses run_model_tool_loop from chat.py so UI and CLI share the same agent loop.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

# Ensure starter_v0 is on sys.path when run via `streamlit run app.py`
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import build_artifact_version, artifact_version_dict
from chat import run_model_tool_loop, write_transcript, now_iso, safe_slug, trim_history

load_lab_env(ROOT)

ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Research Agent · Day 04",
    page_icon="🔬",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark gradient background */
.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
}

/* Main container */
section.main > div {
    padding-top: 1rem;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.04);
    border-right: 1px solid rgba(255,255,255,0.08);
}
[data-testid="stSidebar"] * {
    color: #e0e0e0 !important;
}

/* Header */
.agent-header {
    text-align: center;
    padding: 1.5rem 0 0.5rem;
}
.agent-header h1 {
    font-size: 2.2rem;
    font-weight: 700;
    background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
}
.agent-header p {
    color: #94a3b8;
    font-size: 0.95rem;
    margin: 0;
}

/* Status badge */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.03em;
}
.badge-pass { background: rgba(52,211,153,0.15); color: #34d399; border: 1px solid rgba(52,211,153,0.3); }
.badge-wait { background: rgba(251,191,36,0.15); color: #fbbf24; border: 1px solid rgba(251,191,36,0.3); }
.badge-error { background: rgba(248,113,113,0.15); color: #f87171; border: 1px solid rgba(248,113,113,0.3); }

/* Chat messages */
.chat-bubble {
    display: flex;
    gap: 12px;
    margin-bottom: 1.2rem;
    animation: fadeUp 0.3s ease;
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
.chat-bubble.user { flex-direction: row-reverse; }
.bubble-avatar {
    width: 36px; height: 36px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0;
}
.avatar-user { background: linear-gradient(135deg, #6366f1, #8b5cf6); }
.avatar-agent { background: linear-gradient(135deg, #0ea5e9, #6366f1); }
.bubble-body { max-width: 80%; }
.bubble-text {
    padding: 12px 16px;
    border-radius: 16px;
    font-size: 0.93rem;
    line-height: 1.6;
    color: #f0f4f8;
    word-break: break-word;
}
.bubble-text.user-text {
    background: linear-gradient(135deg, rgba(99,102,241,0.4), rgba(139,92,246,0.4));
    border: 1px solid rgba(139,92,246,0.3);
    border-top-right-radius: 4px;
}
.bubble-text.agent-text {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    border-top-left-radius: 4px;
}
.bubble-time {
    font-size: 0.7rem;
    color: #64748b;
    margin-top: 4px;
    padding: 0 4px;
}
.chat-bubble.user .bubble-time { text-align: right; }

/* Tool trace card */
.tool-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-left: 3px solid #6366f1;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 0.82rem;
    color: #cbd5e1;
    font-family: 'Courier New', monospace;
}
.tool-card.error { border-left-color: #f87171; }
.tool-name { font-weight: 700; color: #a78bfa; }
.tool-ok { color: #34d399; }
.tool-err { color: #f87171; }

/* Input area */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 12px !important;
    color: #f0f4f8 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 12px 16px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.2) !important;
}
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(99,102,241,0.5) !important;
}

/* Divider */
hr { border-color: rgba(255,255,255,0.08) !important; }

/* Metric cards */
.metric-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 14px 18px;
    text-align: center;
}
.metric-value { font-size: 1.6rem; font-weight: 700; color: #a78bfa; }
.metric-label { font-size: 0.75rem; color: #64748b; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
def init_state() -> None:
    defaults = {
        "messages": [],       # list of {role, content, time, rounds, tool_events}
        "history": [],        # for trim_history (raw role/content pairs)
        "transcript": None,
        "transcript_path": None,
        "turn_index": 0,
        "total_tools_called": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"], index=0)
    version_label = st.text_input("Version label", value="v1", help="e.g. v0, v1, v2")
    max_tool_rounds = st.slider("Max tool rounds", 1, 8, 4)
    history_window = st.slider("History window", 0, 10, 5)

    st.markdown("---")
    st.markdown("## 📊 Session Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{st.session_state.turn_index}</div>
            <div class="metric-label">Turns</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{st.session_state.total_tools_called}</div>
            <div class="metric-label">Tool calls</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🗑️ Clear chat", use_container_width=True):
        for k in ["messages", "history", "transcript", "transcript_path", "turn_index", "total_tools_called"]:
            st.session_state[k] = [] if k in ("messages", "history") else (None if k in ("transcript", "transcript_path") else 0)
        st.rerun()

    if st.session_state.transcript_path:
        st.markdown(f"**Transcript:** `{Path(st.session_state.transcript_path).name}`")

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="agent-header">
    <h1>🔬 Research Agent</h1>
    <p>Day 04 · AI20k · Powered by multi-tool research pipeline</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# ── Load provider + tools (cached per config) ─────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_provider(name: str):
    return make_provider(name)

@st.cache_resource(show_spinner=False)
def get_tools():
    decls = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
    return to_openai_tools(decls)

@st.cache_resource(show_spinner=False)
def get_system_prompt() -> str:
    p = ARTIFACTS_DIR / "system_prompt.md"
    return p.read_text(encoding="utf-8") if p.exists() else "You are a helpful research assistant."

# ── Render chat history ────────────────────────────────────────────────────────
chat_container = st.container()

def render_tool_trace(rounds: list) -> None:
    if not rounds:
        return
    total = sum(len(r.get("tool_calls", [])) for r in rounds)
    if total == 0:
        return
    with st.expander(f"🔧 Tool trace · {total} call(s) across {len(rounds)} round(s)", expanded=False):
        for r in rounds:
            calls = r.get("tool_calls", [])
            results = r.get("tool_results", [])
            if not calls:
                continue
            st.markdown(f"**Round {r['round']}**")
            for i, call in enumerate(calls):
                res = results[i] if i < len(results) else {}
                err = res.get("result", {}).get("error") if isinstance(res.get("result"), dict) else None
                status_cls = "error" if err else ""
                status_icon = f'<span class="tool-err">✗ {err}</span>' if err else '<span class="tool-ok">✓ ok</span>'
                args_str = json.dumps(call.get("args", {}), ensure_ascii=False)
                st.markdown(
                    f'<div class="tool-card {status_cls}">'
                    f'<span class="tool-name">⚡ {call["name"]}</span> '
                    f'<code>{args_str}</code> → {status_icon}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

with chat_container:
    if not st.session_state.messages:
        st.markdown("""
        <div style="text-align:center; padding: 3rem 0; color: #475569;">
            <div style="font-size:3rem; margin-bottom:1rem;">🔬</div>
            <div style="font-size:1.1rem; font-weight:500; color:#94a3b8;">
                Hỏi agent để nghiên cứu bất kỳ chủ đề nào
            </div>
            <div style="font-size:0.85rem; margin-top:0.5rem; color:#475569;">
                Web search · Firecrawl · Twitter · arXiv
            </div>
        </div>
        """, unsafe_allow_html=True)

    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]
        time_str = msg.get("time", "")
        is_user = role == "user"

        avatar_cls = "avatar-user" if is_user else "avatar-agent"
        avatar_icon = "👤" if is_user else "🤖"
        bubble_cls = "user-text" if is_user else "agent-text"
        bubble_dir = "user" if is_user else ""

        st.markdown(f"""
        <div class="chat-bubble {bubble_dir}">
            <div class="bubble-avatar {avatar_cls}">{avatar_icon}</div>
            <div class="bubble-body">
                <div class="bubble-text {bubble_cls}">{content}</div>
                <div class="bubble-time">{time_str}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not is_user and msg.get("rounds"):
            render_tool_trace(msg["rounds"])

# ── Input form ─────────────────────────────────────────────────────────────────
st.markdown("---")
with st.form("chat_form", clear_on_submit=True):
    cols = st.columns([8, 1])
    with cols[0]:
        user_input = st.text_input(
            "Your question",
            placeholder="VD: Tweet mới nhất của Sam Altman là gì? / Tìm paper về LLM agents...",
            label_visibility="collapsed",
        )
    with cols[1]:
        submitted = st.form_submit_button("Send ➤", use_container_width=True)

# ── Handle submission ──────────────────────────────────────────────────────────
if submitted and user_input.strip():
    user_text = user_input.strip()
    now = datetime.now().strftime("%H:%M:%S")

    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_text, "time": now})
    st.session_state.history.append({"role": "user", "content": user_text})

    # Init transcript on first turn
    if st.session_state.transcript is None:
        ts = datetime.now().strftime("%Y%m%dT%H%M%S%f")
        tid = f"{safe_slug(version_label)}_{safe_slug(provider_name)}_{ts}"
        tp = TRANSCRIPTS_DIR / f"{tid}.transcript.json"
        av = build_artifact_version(version_label, ARTIFACTS_DIR / "system_prompt.md", ARTIFACTS_DIR / "tools.yaml")
        st.session_state.transcript = {
            "transcript_id": tid,
            **artifact_version_dict(av),
            "provider": provider_name,
            "model": None,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "turns": [],
        }
        st.session_state.transcript_path = str(tp)

    # Run agent
    with st.spinner("🔍 Agent đang nghiên cứu..."):
        try:
            provider = get_provider(provider_name)
            tools = get_tools()
            system_prompt = get_system_prompt()

            messages = [
                {"role": "system", "content": system_prompt},
                *trim_history(st.session_state.history[:-1], history_window),
                {"role": "user", "content": user_text},
            ]

            result = run_model_tool_loop(
                provider=provider,
                messages=messages,
                tools=tools,
                model=None,
                max_tool_rounds=max_tool_rounds,
            )
            assistant_text = result["assistant_text"]
            rounds = result.get("rounds", [])
            tool_events = result.get("tool_events", [])
            status = result.get("status", "answered")

            # Count tool calls
            n_calls = sum(len(r.get("tool_calls", [])) for r in rounds)
            st.session_state.total_tools_called += n_calls

            # Save to history
            st.session_state.history.append({"role": "assistant", "content": assistant_text})
            st.session_state.turn_index += 1

            # Add agent message
            agent_time = datetime.now().strftime("%H:%M:%S")
            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_text,
                "time": agent_time,
                "rounds": rounds,
                "tool_events": tool_events,
                "status": status,
            })

            # Save transcript
            turn_record = {
                "turn_index": st.session_state.turn_index,
                "started_at": now_iso(),
                "ended_at": now_iso(),
                "user": user_text,
                **result,
            }
            st.session_state.transcript["turns"].append(turn_record)
            write_transcript(Path(st.session_state.transcript_path), st.session_state.transcript)

        except Exception as exc:
            err_msg = f"❌ Lỗi: {type(exc).__name__}: {exc}"
            st.session_state.messages.append({
                "role": "assistant",
                "content": err_msg,
                "time": datetime.now().strftime("%H:%M:%S"),
                "rounds": [],
            })

    st.rerun()
