from __future__ import annotations

import json
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

import streamlit as st

from chat import run_model_tool_loop, write_transcript
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


ROOT = Path(__file__).parent
ARTIFACTS = ROOT / "artifacts"
RUNS = ROOT / "runs"
TRANSCRIPTS = ROOT / "transcripts"
SYSTEM_PROMPT_PATH = ARTIFACTS / "system_prompt.md"
TOOLS_PATH = ARTIFACTS / "tools.yaml"
REPLAY_ARTIFACTS = ARTIFACTS / "versions"
DEMO_SCRIPT_PATH = ROOT / "DEMO_SCRIPT.md"

VERSION_ARTIFACTS: dict[str, dict[str, Any]] = {
    "v3": {
        "prompt": REPLAY_ARTIFACTS / "v3" / "system_prompt.md",
        "tools": REPLAY_ARTIFACTS / "v3" / "tools.yaml",
        "mode": "Exact final snapshot",
        "historical": True,
    },
    "v2": {
        "prompt": REPLAY_ARTIFACTS / "v2" / "system_prompt.md",
        "tools": REPLAY_ARTIFACTS / "v2" / "tools.yaml",
        "mode": "Replay reconstruction",
        "historical": False,
    },
    "v1": {
        "prompt": REPLAY_ARTIFACTS / "v1" / "system_prompt.md",
        "tools": REPLAY_ARTIFACTS / "v1" / "tools.yaml",
        "mode": "Replay reconstruction",
        "historical": False,
    },
    "v0": {
        "prompt": REPLAY_ARTIFACTS / "v0" / "system_prompt.md",
        "tools": REPLAY_ARTIFACTS / "v0" / "tools.yaml",
        "mode": "Exact starter baseline",
        "historical": True,
    },
}

DEMO_SCENARIOS: dict[str, dict[str, Any]] = {
    "01 · Multi-source routing": {
        "case_id": "R13_parallel_web_and_tweets",
        "prompts": ["Tìm trên web tin AI hôm nay và tìm thêm tweet về AI."],
        "expected": "v3: lookup(news, day) + social_search(AI)",
        "clean_rule": "Clean before starting this independent scenario.",
    },
    "02 · Missing information": {
        "case_id": "R10_missing_handle",
        "prompts": [
            "Tóm tắt 5 tweet mới nhất giúp mình.",
            "Của Elon Musk nhé, giữ đúng 5 tweet.",
        ],
        "expected": "v3: clarify(text), then timeline(elonmusk, limit=5)",
        "clean_rule": "Do not clean between these two turns.",
    },
    "03 · Confirmation boundary": {
        "case_id": "R12_confirm_before_send",
        "prompts": ["Đăng bản tin này lên Telegram giúp mình."],
        "expected": "v3: clarify(response_type=yes_no); never send directly",
        "clean_rule": "Clean before starting this independent scenario.",
    },
    "Backup · Channel switch": {
        "case_id": "M06_switch_tool",
        "prompts": [
            "Mọi người nói gì về OpenAI trên Twitter?",
            "Bỏ Twitter, chuyển sang tìm trên web tin tức đi.",
            "Giữ chủ đề OpenAI.",
        ],
        "expected": "v3 final intent: lookup(OpenAI, news) only",
        "clean_rule": "Do not clean between the three turns.",
    },
}

load_lab_env(ROOT)

st.set_page_config(
    page_title="Research Agent · Evidence Studio",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      :root {
        --ink: #14221b;
        --muted: #617069;
        --paper: #f4f6ef;
        --panel: #ffffff;
        --forest: #113f2b;
        --mint: #dff3e8;
        --lime: #c9ef73;
        --amber: #efb44d;
        --line: #dbe3dc;
      }
      .stApp {
        background:
          radial-gradient(circle at 78% 8%, rgba(201,239,115,.26), transparent 24rem),
          linear-gradient(180deg, #f8faf5 0%, var(--paper) 100%);
        color: var(--ink);
      }
      [data-testid="stSidebar"] {
        background: #0f2f22;
        border-right: 1px solid rgba(255,255,255,.08);
      }
      [data-testid="stSidebar"] * { color: #eef7f0; }
      [data-testid="stSidebar"] .stSelectbox label,
      [data-testid="stSidebar"] .stSlider label { color: #bcd0c4 !important; }
      .hero {
        padding: 2rem 2.1rem;
        border-radius: 24px;
        background: linear-gradient(122deg, #103c29 0%, #1e6041 72%, #2a7951 100%);
        box-shadow: 0 18px 50px rgba(17,63,43,.15);
        color: white;
        margin-bottom: 1.1rem;
        position: relative;
        overflow: hidden;
      }
      .hero:after {
        content: "";
        position: absolute;
        width: 260px; height: 260px; border-radius: 50%;
        right: -55px; top: -115px;
        border: 42px solid rgba(201,239,115,.15);
      }
      .eyebrow {
        font-size: .76rem; letter-spacing: .17em; text-transform: uppercase;
        color: #cdf285; font-weight: 750; margin-bottom: .55rem;
      }
      .hero h1 {
        font-size: clamp(2rem, 4.5vw, 4.2rem);
        letter-spacing: -.055em; line-height: .98;
        margin: 0; max-width: 780px; color: #fff;
      }
      .hero p { color: #d7e7dc; max-width: 720px; font-size: 1.02rem; margin: .9rem 0 0; }
      .status-row { display:flex; gap:.55rem; flex-wrap:wrap; margin-top:1.2rem; }
      .pill {
        border: 1px solid rgba(255,255,255,.18); border-radius: 999px;
        padding: .34rem .72rem; color:#eaf5ed; font-size:.78rem;
        background: rgba(255,255,255,.07);
      }
      .pill.live { background:#c9ef73; color:#173322; border-color:#c9ef73; font-weight:750; }
      div[data-testid="stMetric"] {
        background: rgba(255,255,255,.86);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 1rem 1.05rem;
        box-shadow: 0 8px 26px rgba(20,34,27,.04);
      }
      div[data-testid="stMetric"] label { color: var(--muted); }
      div[data-testid="stMetricValue"] { color: var(--forest); letter-spacing:-.04em; }
      div[data-testid="stExpander"] {
        background: rgba(255,255,255,.88);
        border: 1px solid var(--line);
        border-radius: 16px;
        overflow: hidden;
      }
      .trace-title { display:flex; align-items:center; gap:.55rem; font-weight:760; color:var(--forest); }
      .trace-dot { width:9px; height:9px; border-radius:50%; background:#50a96f; box-shadow:0 0 0 5px #e4f4e9; }
      .trace-call-head {
        display:flex; align-items:center; justify-content:space-between; gap:.8rem;
        margin:.1rem 0 .85rem; padding-bottom:.7rem; border-bottom:1px solid #e4ebe5;
      }
      .trace-status {
        border-radius:999px; padding:.22rem .58rem; font-size:.7rem; font-weight:760;
        letter-spacing:.06em; background:#e3f4e9; color:#276a43; border:1px solid #c9e7d3;
      }
      .trace-status.error { background:#fff0ed; color:#a73b2b; border-color:#f2cbc4; }
      .trace-section-label {
        color:#6c7b73; font-size:.7rem; font-weight:780; letter-spacing:.1em;
        text-transform:uppercase; margin:.15rem 0 .45rem;
      }
      .trace-args-grid {
        display:grid; grid-template-columns:repeat(auto-fit, minmax(150px, 1fr));
        gap:.55rem; margin-bottom:1rem;
      }
      .trace-arg {
        min-width:0; background:#f5f8f5; border:1px solid #dfe8e1;
        border-radius:12px; padding:.65rem .75rem;
      }
      .trace-arg-key {
        color:#718078; font-size:.67rem; font-weight:760; letter-spacing:.06em;
        text-transform:uppercase; margin-bottom:.22rem;
      }
      .trace-arg-value {
        color:#183426; font-family:ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size:.82rem; line-height:1.35; overflow-wrap:anywhere;
      }
      .trace-summary {
        display:flex; align-items:center; justify-content:space-between; gap:.7rem;
        background:#173f2d; color:#fff; border-radius:13px; padding:.72rem .85rem;
        margin-bottom:.6rem;
      }
      .trace-summary strong { color:#fff; font-size:.92rem; }
      .trace-summary span { color:#cee1d5; font-size:.76rem; }
      .source-card {
        display:grid; grid-template-columns:2rem minmax(0,1fr) auto; gap:.7rem;
        align-items:start; background:#fff; border:1px solid #dfe7e1;
        border-radius:13px; padding:.72rem .78rem; margin:.48rem 0;
        box-shadow:0 5px 16px rgba(20,34,27,.035);
      }
      .source-rank {
        display:grid; place-items:center; width:1.8rem; height:1.8rem;
        border-radius:9px; background:#e8f4ec; color:#236842; font-weight:780;
        font-size:.75rem;
      }
      .source-title {
        display:block; color:#163b29 !important; font-weight:740; line-height:1.3;
        text-decoration:none; overflow-wrap:anywhere;
      }
      .source-title:hover { text-decoration:underline; }
      .source-meta { color:#718078; font-size:.72rem; margin-top:.18rem; }
      .source-summary {
        color:#53645b; font-size:.76rem; line-height:1.42; margin-top:.35rem;
        display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;
        overflow:hidden;
      }
      .source-score {
        white-space:nowrap; border-radius:999px; background:#eef7d8; color:#42611d;
        padding:.2rem .46rem; font-size:.67rem; font-weight:740;
      }
      .trace-kv {
        background:#f7f9f7; border:1px solid #e1e8e2; border-radius:12px;
        padding:.68rem .78rem; margin:.45rem 0 .75rem; color:#31473b;
        font-size:.8rem; line-height:1.55; overflow-wrap:anywhere;
      }
      .trace-kv b { color:#173f2d; }
      .raw-hint { color:#7a8880; font-size:.7rem; margin:.65rem 0 .25rem; }
      @media (max-width: 760px) {
        .source-card { grid-template-columns:2rem minmax(0,1fr); }
        .source-score { grid-column:2; justify-self:start; }
      }
      .artifact {
        border-left: 4px solid var(--lime);
        background: #fff;
        padding: .85rem 1rem;
        border-radius: 0 14px 14px 0;
        color: var(--muted);
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: .8rem;
      }
      .demo-card {
        background:#fff; border:1px solid var(--line); border-radius:18px;
        padding:1.05rem 1.1rem; height:100%;
      }
      .demo-card b { color:var(--forest); }
      .demo-deck {
        background:linear-gradient(135deg,#f7faf6,#eef6e8);
        border:1px solid #dce8dd; border-radius:16px; padding:.85rem .95rem;
        margin:.25rem 0 .75rem;
      }
      .demo-deck-label {
        color:#6d7c73; font-size:.68rem; font-weight:780; letter-spacing:.1em;
        text-transform:uppercase; margin-bottom:.35rem;
      }
      .demo-deck-prompt {
        color:#173f2d; font-weight:720; line-height:1.45; margin-bottom:.35rem;
      }
      .demo-deck-meta { color:#64746b; font-size:.74rem; line-height:1.4; }
      .artifact-mode {
        border-radius:10px; padding:.55rem .68rem; margin:.45rem 0;
        background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.12);
        color:#d8e8de; font-size:.72rem; line-height:1.45;
      }
      .artifact-mode b { color:#cfee87; }
      .version-notice {
        border-left:4px solid #efb44d; background:#fff8e8; color:#684d19;
        border-radius:0 12px 12px 0; padding:.68rem .8rem; font-size:.78rem;
        margin:.35rem 0 .75rem;
      }
      .stTabs [data-baseweb="tab-list"] { gap:.45rem; }
      .stTabs [role="tab"] {
        border-radius:999px !important;
        padding:.45rem .95rem !important;
        background:#e7eee8 !important;
        border:1px solid #d3dfd6 !important;
        transition:background-color .16s ease, border-color .16s ease;
      }
      .stTabs [role="tab"] p,
      .stTabs [role="tab"] span,
      .stTabs [role="tab"] > div {
        color:#29483a !important;
        font-weight:680 !important;
      }
      .stTabs [role="tab"]:hover {
        background:#dce8df !important;
        border-color:#bdd1c2 !important;
      }
      .stTabs [role="tab"][aria-selected="true"] {
        background:#173f2d !important;
        border-color:#173f2d !important;
      }
      .stTabs [role="tab"][aria-selected="true"] p,
      .stTabs [role="tab"][aria-selected="true"] span,
      .stTabs [role="tab"][aria-selected="true"] > div {
        color:#ffffff !important;
      }
      [data-testid="stMainBlockContainer"] {
        color: var(--ink) !important;
      }
      [data-testid="stChatMessage"] {
        background: rgba(255,255,255,.94) !important;
        border: 1px solid #d9e2db !important;
        border-radius: 16px !important;
        box-shadow: 0 7px 22px rgba(20,34,27,.045);
      }
      [data-testid="stChatMessage"] p,
      [data-testid="stChatMessage"] li,
      [data-testid="stChatMessage"] strong {
        color: #172b21 !important;
      }
      [data-testid="stChatInput"] textarea {
        color: #f7faf8 !important;
        caret-color: #c9ef73 !important;
      }
      [data-testid="stChatInput"] textarea::placeholder {
        color: #b7bdba !important;
        opacity: 1 !important;
      }
      [data-testid="stMainBlockContainer"] code {
        color:#174c34 !important;
        background:#e8f4ec !important;
        border:1px solid #d1e8d9 !important;
        border-radius:6px !important;
        padding:.08rem .3rem !important;
      }
      [data-testid="stMainBlockContainer"] [data-testid="stJson"] code {
        background: transparent !important;
        border: 0 !important;
        padding: 0 !important;
      }
      footer { visibility:hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def latest_run(version: str, suite: str = "base") -> tuple[Path, dict[str, Any]] | None:
    candidates = sorted(RUNS.glob(f"{version}_B_{suite}_*.json"), key=lambda path: path.stat().st_mtime)
    if not candidates:
        return None
    path = candidates[-1]
    return path, read_json(path)


def latest_runs_by_version() -> dict[str, tuple[Path, dict[str, Any]]]:
    found: dict[str, tuple[Path, dict[str, Any]]] = {}
    for version in ("v0", "v1", "v2", "v3"):
        item = latest_run(version)
        if item:
            found[version] = item
    return found


def ensure_session(
    version: str,
    provider_name: str,
    model: str | None,
    artifact: Any,
    system_prompt_path: Path,
    tools_path: Path,
) -> None:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "turn_traces" not in st.session_state:
        st.session_state.turn_traces = []
    if "ui_transcript" not in st.session_state:
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
        transcript_id = f"ui_{version}_{provider_name}_{timestamp}"
        st.session_state.transcript_path = TRANSCRIPTS / f"{transcript_id}.transcript.json"
        st.session_state.ui_transcript = {
            "transcript_id": transcript_id,
            **artifact_version_dict(artifact),
            "provider": provider_name,
            "model": model,
            "system_prompt": str(system_prompt_path),
            "tools": str(tools_path),
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "source": "streamlit_ui",
            "turns": [],
        }


def reset_session(
    version: str,
    provider_name: str,
    model: str | None,
    artifact: Any,
    system_prompt_path: Path,
    tools_path: Path,
) -> None:
    for key in ("chat_history", "turn_traces", "ui_transcript", "transcript_path"):
        st.session_state.pop(key, None)
    ensure_session(
        version,
        provider_name,
        model,
        artifact,
        system_prompt_path,
        tools_path,
    )


def compact_result(result: Any) -> Any:
    if not isinstance(result, dict):
        return result
    return {
        key: value
        for key, value in result.items()
        if key in {"error", "message", "status", "item_count", "title", "url", "markdown", "tier_counts", "items"}
    }


def display_value(value: Any, limit: int = 180) -> str:
    if isinstance(value, (dict, list)):
        rendered = json.dumps(value, ensure_ascii=False, separators=(", ", ": "))
    elif value is None:
        rendered = "—"
    else:
        rendered = str(value)
    if len(rendered) > limit:
        rendered = f"{rendered[:limit - 1]}…"
    return rendered


def render_arguments(args: Any) -> None:
    safe_args = args if isinstance(args, dict) else {"value": args}
    cards = []
    for key, value in safe_args.items():
        cards.append(
            "<div class='trace-arg'>"
            f"<div class='trace-arg-key'>{escape(str(key))}</div>"
            f"<div class='trace-arg-value'>{escape(display_value(value))}</div>"
            "</div>"
        )
    if not cards:
        cards.append(
            "<div class='trace-arg'><div class='trace-arg-value'>No arguments</div></div>"
        )
    st.markdown(
        "<div class='trace-section-label'>Request arguments</div>"
        f"<div class='trace-args-grid'>{''.join(cards)}</div>",
        unsafe_allow_html=True,
    )


def render_result_summary(result: Any, error: Any) -> None:
    if not isinstance(result, dict):
        st.markdown(
            "<div class='trace-section-label'>Tool output</div>"
            f"<div class='trace-kv'>{escape(display_value(result, 600))}</div>",
            unsafe_allow_html=True,
        )
        return

    items = result.get("items")
    item_list = items if isinstance(items, list) else []
    if item_list:
        source_cards = []
        for rank, item in enumerate(item_list[:3], start=1):
            if not isinstance(item, dict):
                continue
            title = escape(str(item.get("title") or "Untitled result"))
            url = escape(str(item.get("url") or "#"), quote=True)
            source = escape(str(item.get("source") or "Unknown source"))
            summary = escape(display_value(item.get("summary") or "No summary available.", 280))
            score = item.get("score")
            score_text = f"{float(score):.0%} match" if isinstance(score, (int, float)) else "source"
            source_cards.append(
                "<div class='source-card'>"
                f"<div class='source-rank'>{rank:02d}</div>"
                "<div>"
                f"<a class='source-title' href='{url}' target='_blank'>{title}</a>"
                f"<div class='source-meta'>{source}</div>"
                f"<div class='source-summary'>{summary}</div>"
                "</div>"
                f"<span class='source-score'>{escape(score_text)}</span>"
                "</div>"
            )
        hidden_count = max(0, len(item_list) - len(source_cards))
        extra_text = f" · {hidden_count} more in raw data" if hidden_count else ""
        st.markdown(
            "<div class='trace-section-label'>Tool output</div>"
            "<div class='trace-summary'>"
            f"<strong>{len(item_list)} sources returned</strong>"
            f"<span>Top matches shown{escape(extra_text)}</span>"
            "</div>"
            f"{''.join(source_cards)}",
            unsafe_allow_html=True,
        )
        return

    summary_rows = []
    for key in ("status", "message", "item_count", "title", "url", "tier_counts"):
        if key in result and result.get(key) is not None:
            summary_rows.append(
                f"<div><b>{escape(key.replace('_', ' ').title())}:</b> "
                f"{escape(display_value(result[key], 360))}</div>"
            )
    if error and not summary_rows:
        summary_rows.append(f"<div><b>Error:</b> {escape(str(error))}</div>")
    if not summary_rows:
        summary_rows.append("<div>Tool completed successfully. Open raw data for details.</div>")
    st.markdown(
        "<div class='trace-section-label'>Tool output</div>"
        f"<div class='trace-kv'>{''.join(summary_rows)}</div>",
        unsafe_allow_html=True,
    )


def render_trace(trace: dict[str, Any], prefix: str) -> None:
    rounds = trace.get("rounds") or []
    if trace.get("error"):
        st.error(trace["error"])
    if not rounds:
        if not trace.get("error"):
            st.info("No tool was required for this request.")
        return
    for round_record in rounds:
        calls = round_record.get("tool_calls") or []
        results = round_record.get("tool_results") or []
        status = "answered" if not calls else "executed"
        label = f"Round {round_record.get('round')} · {len(calls)} tool call(s) · {status}"
        with st.expander(label, expanded=True):
            if not calls:
                st.caption("Model answered directly without a tool.")
            for index, call in enumerate(calls):
                result_event = results[index] if index < len(results) else {}
                result = result_event.get("result", {})
                error = result.get("error") if isinstance(result, dict) else None
                st.markdown(
                    "<div class='trace-call-head'>"
                    f"<div class='trace-title'><span class='trace-dot'></span>"
                    f"{escape(str(call.get('name', 'unknown')))}</div>"
                    f"<span class='trace-status{' error' if error else ''}'>"
                    f"{'ERROR' if error else 'SUCCESS'}</span>"
                    "</div>",
                    unsafe_allow_html=True,
                )
                render_arguments(call.get("args", {}))
                render_result_summary(result, error)
                if error:
                    st.error(f"{error}: {result.get('message', '')}")
                st.markdown(
                    "<div class='raw-hint'>Raw event · expand only when debugging</div>",
                    unsafe_allow_html=True,
                )
                st.json(
                    {"arguments": call.get("args", {}), "result": compact_result(result)},
                    expanded=False,
                )


def run_live_request(
    user_text: str,
    provider_name: str,
    model: str | None,
    max_rounds: int,
    system_prompt: str,
    openai_tools: list[dict[str, Any]],
) -> dict[str, Any]:
    provider = make_provider(provider_name)
    recent_history = st.session_state.chat_history[-10:]
    messages = [
        {"role": "system", "content": system_prompt},
        *recent_history,
        {"role": "user", "content": user_text},
    ]
    return run_model_tool_loop(
        provider=provider,
        messages=messages,
        tools=openai_tools,
        model=model or None,
        max_tool_rounds=max_rounds,
    )


with st.sidebar:
    st.markdown("### ◈ Evidence Studio")
    st.caption("Research agent control room")
    provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"], index=0)
    version = st.selectbox(
        "Live artifact",
        list(VERSION_ARTIFACTS),
        index=0,
        help="Changing version loads its prompt/tool snapshot and starts a clean transcript.",
    )
    model = st.text_input("Model override", value="", placeholder="Use provider default")
    max_rounds = st.slider("Maximum tool rounds", min_value=1, max_value=6, value=4)

    artifact_config = VERSION_ARTIFACTS[version]
    active_prompt_path = Path(artifact_config["prompt"])
    active_tools_path = Path(artifact_config["tools"])
    system_prompt = active_prompt_path.read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(active_tools_path)
    openai_tools = to_openai_tools(tool_declarations)
    artifact = build_artifact_version(version, active_prompt_path, active_tools_path)

    session_signature = "|".join(
        [artifact.artifact_version, provider_name, model or "provider-default"]
    )
    previous_signature = st.session_state.get("active_session_signature")
    if previous_signature != session_signature:
        reset_session(
            version,
            provider_name,
            model or None,
            artifact,
            active_prompt_path,
            active_tools_path,
        )
        st.session_state.active_session_signature = session_signature
        st.session_state.pop("active_demo_scenario", None)
        st.session_state.pop("active_demo_step", None)
    else:
        ensure_session(
            version,
            provider_name,
            model or None,
            artifact,
            active_prompt_path,
            active_tools_path,
        )

    st.markdown("---")
    st.caption("CURRENT ARTIFACT")
    st.code(artifact.artifact_version, language=None)
    st.markdown(
        "<div class='artifact-mode'><b>"
        f"{escape(str(artifact_config['mode']))}</b><br>"
        "Changing Live artifact automatically starts a clean transcript."
        "</div>",
        unsafe_allow_html=True,
    )
    st.caption(f"{len(tool_declarations)} tools exposed")
    if st.button("Start a clean demo", use_container_width=True):
        reset_session(
            version,
            provider_name,
            model or None,
            artifact,
            active_prompt_path,
            active_tools_path,
        )
        st.session_state.pop("active_demo_scenario", None)
        st.session_state.pop("active_demo_step", None)
        st.rerun()

latest_selected_run = latest_run(version)
summary = latest_selected_run[1]["summary"] if latest_selected_run else {}

st.markdown(
    f"""
    <section class="hero">
      <div class="eyebrow">Research Agent · Live Evidence</div>
      <h1>Every answer leaves a trace.</h1>
      <p>Run the agent, inspect every tool decision, and compare prompt versions
      with evidence captured from real API executions.</p>
      <div class="status-row">
        <span class="pill live">● LIVE READY</span>
        <span class="pill">{artifact.artifact_version}</span>
        <span class="pill">{escape(str(artifact_config['mode']))}</span>
        <span class="pill">{len(tool_declarations)} tools</span>
        <span class="pill">transcript on</span>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)

metric_cols = st.columns(4)
metric_cols[0].metric(f"{version} base accuracy", f"{summary.get('case_accuracy', 0):.0%}")
metric_cols[1].metric("Tool routing", f"{summary.get('tool_routing_accuracy', 0):.0%}")
metric_cols[2].metric("Multi-turn", f"{summary.get('multiturn_accuracy', 0):.0%}")
metric_cols[3].metric("Provider errors", summary.get("provider_error_cases", "—"))

live_tab, versions_tab, evidence_tab, guide_tab = st.tabs(
    ["Live agent", "Version lab", "Evidence vault", "Showdown guide"]
)

with live_tab:
    left, right = st.columns([.95, 1.05], gap="large")
    with left:
        st.subheader("Live conversation")
        st.caption("Try research, missing-information, source-triage, and boundary scenarios.")

        demo_prompt: str | None = None
        with st.expander("Presenter prompt deck", expanded=not st.session_state.chat_history):
            selected_demo_name = st.selectbox(
                "Scenario",
                list(DEMO_SCENARIOS),
                key="demo_scenario_choice",
            )
            selected_demo = DEMO_SCENARIOS[selected_demo_name]
            st.caption(
                f"Eval case: {selected_demo['case_id']} · {selected_demo['clean_rule']}"
            )
            st.markdown(
                "<div class='demo-deck'>"
                "<div class='demo-deck-label'>Target evidence · final v3</div>"
                f"<div class='demo-deck-meta'>{escape(selected_demo['expected'])}</div>"
                "</div>",
                unsafe_allow_html=True,
            )
            if st.button(
                "Reset & load this scenario",
                use_container_width=True,
                key="load_demo_scenario",
            ):
                reset_session(
                    version,
                    provider_name,
                    model or None,
                    artifact,
                    active_prompt_path,
                    active_tools_path,
                )
                st.session_state.active_demo_scenario = selected_demo_name
                st.session_state.active_demo_step = 0
                st.rerun()

            active_demo_name = st.session_state.get("active_demo_scenario")
            if active_demo_name:
                active_demo = DEMO_SCENARIOS[active_demo_name]
                active_step = int(st.session_state.get("active_demo_step", 0))
                if active_step < len(active_demo["prompts"]):
                    next_prompt = active_demo["prompts"][active_step]
                    st.markdown(
                        "<div class='demo-deck'>"
                        f"<div class='demo-deck-label'>Next prompt · "
                        f"{active_step + 1}/{len(active_demo['prompts'])}</div>"
                        f"<div class='demo-deck-prompt'>{escape(next_prompt)}</div>"
                        f"<div class='demo-deck-meta'>{escape(active_demo['clean_rule'])}</div>"
                        "</div>",
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "Run next demo prompt",
                        type="primary",
                        use_container_width=True,
                        key="run_demo_prompt",
                    ):
                        demo_prompt = next_prompt
                        st.session_state.active_demo_step = active_step + 1
                else:
                    st.success("Scenario complete. Start another scenario to reset the transcript.")

        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        manual_prompt = st.chat_input("Ask the research agent…")
        prompt = demo_prompt or manual_prompt
        if prompt:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            started_at = now_iso()
            with st.chat_message("assistant"):
                with st.spinner("Selecting and executing tools…"):
                    try:
                        result = run_live_request(
                            prompt,
                            provider_name,
                            model or None,
                            max_rounds,
                            system_prompt,
                            openai_tools,
                        )
                        answer = result.get("assistant_text") or "No response returned."
                        st.markdown(answer)
                    except Exception as exc:
                        result = {
                            "status": "provider_error",
                            "assistant_text": "",
                            "rounds": [],
                            "tool_events": [],
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                        answer = "The provider request failed. Open the trace panel for details."
                        st.error(result["error"])
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            trace = {
                "turn_index": len(st.session_state.turn_traces) + 1,
                "started_at": started_at,
                "ended_at": now_iso(),
                "user": prompt,
                **result,
            }
            st.session_state.turn_traces.append(trace)
            st.session_state.ui_transcript["turns"].append(trace)
            write_transcript(st.session_state.transcript_path, st.session_state.ui_transcript)
            st.rerun()

    with right:
        st.subheader("Tool trace")
        st.caption("Newest turn first · args and results are preserved")
        if st.session_state.turn_traces:
            for trace in reversed(st.session_state.turn_traces):
                st.markdown(f"**Turn {trace['turn_index']}** · `{trace.get('status', 'unknown')}`")
                st.caption(trace.get("user", ""))
                render_trace(trace, f"turn-{trace['turn_index']}")
        else:
            st.info("Run a prompt to generate the first trace.")
        st.markdown(
            f"<div class='artifact'>transcript_id: "
            f"{st.session_state.ui_transcript['transcript_id']}<br>"
            f"artifact_version: {artifact.artifact_version}</div>",
            unsafe_allow_html=True,
        )

with versions_tab:
    st.subheader("Prompt evolution · v0 → v3")
    st.caption("Latest base run for each version. Metrics come directly from saved JSON evidence.")
    st.markdown(
        "<div class='version-notice'><b>Evidence rule:</b> this tab shows the "
        "authoritative historical runs. Live v1/v2 are replay reconstructions "
        "because their exact prompt files were not preserved.</div>",
        unsafe_allow_html=True,
    )
    version_runs = latest_runs_by_version()
    rows: list[dict[str, Any]] = []
    for item_version, (path, payload) in version_runs.items():
        item_summary = payload.get("summary", {})
        rows.append({
            "version": item_version,
            "case_accuracy": item_summary.get("case_accuracy"),
            "routing_accuracy": item_summary.get("tool_routing_accuracy"),
            "argument_accuracy": item_summary.get("argument_accuracy"),
            "multiturn_accuracy": item_summary.get("multiturn_accuracy"),
            "provider_errors": item_summary.get("provider_error_cases"),
            "artifact_version": payload.get("artifact_version"),
            "run_file": path.name,
        })
    if rows:
        chart_rows = {
            row["version"]: {
                "Case accuracy": row["case_accuracy"],
                "Tool routing": row["routing_accuracy"],
                "Arguments": row["argument_accuracy"],
            }
            for row in rows
        }
        st.line_chart(chart_rows, height=330)
        st.dataframe(rows, use_container_width=True, hide_index=True)

        all_case_ids = sorted({
            result["id"]
            for _, payload in version_runs.values()
            for result in payload.get("results", [])
        })
        selected_case = st.selectbox(
            "Compare one scenario across versions",
            all_case_ids,
            index=all_case_ids.index("M06_switch_tool") if "M06_switch_tool" in all_case_ids else 0,
        )
        comparison_cols = st.columns(len(version_runs))
        for column, (item_version, (_, payload)) in zip(comparison_cols, version_runs.items()):
            case = next((item for item in payload.get("results", []) if item["id"] == selected_case), None)
            with column:
                st.markdown(f"### {item_version}")
                if case:
                    passed = case["result"].get("passed")
                    if passed:
                        st.success("PASS")
                    else:
                        st.error("FAIL")
                    st.json(case["result"].get("actual_tool_calls", []), expanded=True)
                    if case["result"].get("failures"):
                        st.caption(" · ".join(case["result"]["failures"]))
                else:
                    st.caption("No evidence")
    else:
        st.warning("No saved base runs found.")

with evidence_tab:
    st.subheader("Evidence vault")
    st.caption("Fallback artifacts remain available even if a live API is slow during the demo.")
    evidence_cols = st.columns(2)
    with evidence_cols[0]:
        st.markdown("#### Run JSON")
        run_files = sorted(RUNS.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
        for path in run_files[:12]:
            payload = read_json(path)
            item_summary = payload.get("summary", {})
            with st.expander(f"{payload.get('version')} · {payload.get('suite')} · {item_summary.get('case_accuracy', 0):.0%}"):
                st.caption(path.name)
                st.json(item_summary, expanded=True)
                st.download_button(
                    "Download JSON",
                    data=path.read_bytes(),
                    file_name=path.name,
                    mime="application/json",
                    key=f"run-{path.name}",
                )
    with evidence_cols[1]:
        st.markdown("#### Transcript JSON")
        transcript_files = sorted(
            TRANSCRIPTS.glob("*.transcript.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for path in transcript_files[:8]:
            payload = read_json(path)
            with st.expander(f"{payload.get('transcript_id')} · {len(payload.get('turns', []))} turns"):
                st.caption(payload.get("artifact_version", ""))
                st.download_button(
                    "Download transcript",
                    data=path.read_bytes(),
                    file_name=path.name,
                    mime="application/json",
                    key=f"transcript-{path.name}",
                )

with guide_tab:
    st.subheader("Three-minute showdown")
    st.caption("Three rehearsed scenarios, one backup, and a clean transcript for every story.")
    cards = st.columns(3)
    primary_scenarios = list(DEMO_SCENARIOS.items())[:3]
    for column, (title, scenario) in zip(cards, primary_scenarios):
        with column:
            prompt_text = scenario["prompts"][0]
            st.markdown(
                f"<div class='demo-card'><b>{title}</b><br><br>"
                f"<code>{escape(prompt_text)}</code><br><br>"
                f"{escape(scenario['expected'])}</div>",
                unsafe_allow_html=True,
            )
    st.markdown("#### Run order")
    st.markdown(
        "1. Open **Version lab** and select the matching eval case.  \n"
        "2. Return to **Live agent**, choose the Live artifact, then open "
        "**Presenter prompt deck**.  \n"
        "3. Click **Reset & load this scenario**, then **Run next demo prompt**.  \n"
        "4. For multi-turn scenarios, run every step without cleaning in between."
    )
    st.markdown(
        "<div class='version-notice'><b>Artifact switching:</b> changing Live "
        "artifact now loads that version's prompt/tool files and automatically "
        "starts a clean transcript. v1/v2 are marked Replay reconstruction; "
        "Version lab remains the historical source of truth.</div>",
        unsafe_allow_html=True,
    )
    if DEMO_SCRIPT_PATH.exists():
        st.download_button(
            "Download Vietnamese demo script",
            data=DEMO_SCRIPT_PATH.read_bytes(),
            file_name=DEMO_SCRIPT_PATH.name,
            mime="text/markdown",
            use_container_width=True,
        )
    st.markdown("#### Presentation checklist")
    check_cols = st.columns(2)
    with check_cols[0]:
        st.checkbox("Open Version lab on M06_switch_tool", value=True)
        st.checkbox("Keep the latest 100% run ready", value=True)
        st.checkbox("Show artifact version and transcript ID", value=True)
    with check_cols[1]:
        st.checkbox("Do not expose .env or credentials", value=True)
        st.checkbox("Keep fallback run/transcript available", value=True)
        st.checkbox("Test the public link on another device", value=False)
