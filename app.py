"""Streamlit chat UI for the MCP agent.

Connect to one MCP endpoint (full URL) with header ``X-API-Key``
(see ``client.config.build_single_server_config``).

Run API: ``uvicorn main:app`` from repo root. Run UI: ``streamlit run app.py``.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

from client.agent import (
    agent_reply_text,
    ainvoke_with_selective_mcp,
    build_chat_agent,
    format_mcp_auth_error,
)
from client.config import build_single_server_config
from client.mcp_discovery import ServerDiscovery, discover_server
from client.mcp_trace import extract_turn_trace

_REPO = Path(__file__).resolve().parent
load_dotenv(_REPO / ".env")


@st.cache_resource
def chat_agent(api_key: str, mcp_url: str):
    return asyncio.run(build_chat_agent(api_key=api_key, mcp_url=mcp_url))


def _is_auth_failure(exc: Exception) -> bool:
    return format_mcp_auth_error(exc) is not None


def _init_session_state() -> None:
    if "mcp_url" not in st.session_state:
        st.session_state.mcp_url = ""
    if "api_key" not in st.session_state:
        st.session_state.api_key = None
    if "connected" not in st.session_state:
        st.session_state.connected = False
    if "discovery" not in st.session_state:
        st.session_state.discovery = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "mcp_activity_idx" not in st.session_state:
        st.session_state.mcp_activity_idx = None


def _disconnect() -> None:
    st.session_state.connected = False
    st.session_state.discovery = None
    st.session_state.messages = []
    st.session_state.api_key = None
    st.session_state.mcp_url = ""
    st.session_state.mcp_activity_idx = None
    chat_agent.clear()


def _render_discovery(discovery: ServerDiscovery) -> None:
    with st.expander(f"{discovery.name} — `{discovery.url}`"):
        st.markdown("**Tools**")
        if discovery.tools:
            for tool in discovery.tools:
                desc = f" — {tool.description}" if tool.description else ""
                st.markdown(f"- `{tool.name}`{desc}")
        else:
            st.caption("(none)")

        st.markdown("**Resources**")
        if discovery.resources:
            for uri in discovery.resources:
                st.markdown(f"- `{uri}`")
        else:
            st.caption("(none)")

        st.markdown("**Prompts**")
        if discovery.prompts:
            for prompt in discovery.prompts:
                desc = f" — {prompt.description}" if prompt.description else ""
                st.markdown(f"- `{prompt.name}`{desc}")
        else:
            st.caption("(none)")


def _render_mcp_trace_body(trace: dict | None) -> None:
    if trace is None:
        st.caption("No MCP activity recorded for this turn.")
        return

    injected = trace.get("context_injected")
    if injected:
        st.markdown("**Turn-specific MCP context injected**")
        st.text(injected)

    steps = trace.get("steps") or []
    if not steps:
        if not injected:
            st.caption("No tool calls this turn.")
        return

    for i, step in enumerate(steps, start=1):
        if step.get("kind") == "tool_call":
            st.markdown(f"**{i}. Tool call** — `{step.get('name')}`")
            st.json(step.get("args") or {})
        elif step.get("kind") == "tool_result":
            label = step.get("name") or step.get("tool_call_id") or "result"
            st.markdown(f"**{i}. Tool result** — `{label}`")
            st.code(step.get("content") or "")


def _render_mcp_activity_sidebar() -> None:
    idx = st.session_state.mcp_activity_idx
    if idx is None:
        return

    messages = st.session_state.messages
    if idx < 0 or idx >= len(messages):
        st.session_state.mcp_activity_idx = None
        return

    msg = messages[idx]
    if msg.get("role") != "assistant":
        return

    with st.sidebar:
        st.markdown("### MCP Activity")
        if st.button("Close", key="mcp_activity_close"):
            st.session_state.mcp_activity_idx = None
            st.rerun()

        for j in range(idx - 1, -1, -1):
            if messages[j]["role"] == "user":
                st.caption("Turn")
                preview = messages[j]["content"]
                if len(preview) > 200:
                    preview = preview[:200] + "…"
                st.text(preview)
                break

        st.divider()
        _render_mcp_trace_body(msg.get("mcp_trace"))


def _connection_tab() -> None:
    if st.session_state.connected:
        url_value = st.session_state.mcp_url
        key_value = st.session_state.api_key or ""
    else:
        url_value = ""
        key_value = ""

    mcp_url_input = st.text_input(
        "MCP Server URL",
        value=url_value,
        placeholder="http://127.0.0.1:8000/math/mcp",
        disabled=st.session_state.connected,
    )
    api_key_input = st.text_input(
        "API Key",
        type="password",
        value=key_value,
        disabled=st.session_state.connected,
    )

    col_connect, col_disconnect = st.columns(2)
    with col_connect:
        connect_clicked = st.button("Connect", disabled=st.session_state.connected)
    with col_disconnect:
        disconnect_clicked = st.button("Disconnect", disabled=not st.session_state.connected)

    if disconnect_clicked:
        _disconnect()
        st.rerun()

    if connect_clicked:
        entered_url = (mcp_url_input or "").strip()
        entered_key = (api_key_input or "").strip()
        if not entered_url:
            st.error("Enter an MCP server URL.")
        elif not entered_key:
            st.error("Enter an API key.")
        else:
            try:
                mcp_url = entered_url.rstrip("/")
                client = MultiServerMCPClient(
                    build_single_server_config(mcp_url=mcp_url, api_key=entered_key)
                )
                discovery = asyncio.run(discover_server(client, mcp_url=mcp_url))
                st.session_state.connected = True
                st.session_state.discovery = discovery
                st.session_state.api_key = entered_key
                st.session_state.mcp_url = mcp_url
                st.session_state.messages = []
                chat_agent.clear()
                st.rerun()
            except Exception as e:
                msg = format_mcp_auth_error(e) or f"{type(e).__name__}: {e}"
                st.error(msg)

    if st.session_state.connected:
        st.success(f"Connected to `{st.session_state.mcp_url}`")
        if st.session_state.discovery:
            _render_discovery(st.session_state.discovery)


def _chat_tab() -> None:
    if not st.session_state.connected or not st.session_state.api_key:
        st.info("Connect on the Connection tab first.")
        st.stop()

    try:
        bundle = chat_agent(st.session_state.api_key, st.session_state.mcp_url)
    except Exception as e:
        if _is_auth_failure(e):
            _disconnect()
            msg = format_mcp_auth_error(e) or str(e)
            st.error(f"{msg}\n\nPlease connect again on the Connection tab.")
            st.stop()
        st.error(
            f"Could not start the agent. Is the MCP server running, MCP_API_KEY set on the server, "
            f"and GROQ_API_KEY set?\n\n{e}"
        )
        st.stop()

    _render_mcp_activity_sidebar()

    for idx, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m["role"] == "assistant":
                if st.button("MCP Activity", key=f"mcp_activity_{idx}"):
                    st.session_state.mcp_activity_idx = idx
                    st.rerun()

    if prompt := st.chat_input("Ask something…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            mcp_trace: dict | None = None
            with st.spinner("Thinking…"):
                try:
                    payload = {
                        "messages": [
                            {"role": x["role"], "content": x["content"]}
                            for x in st.session_state.messages
                        ]
                    }
                    turn = asyncio.run(ainvoke_with_selective_mcp(bundle, payload["messages"]))
                    reply = agent_reply_text(turn.result)
                    mcp_trace = extract_turn_trace(
                        turn.result["messages"],
                        context_extra=turn.context_extra,
                    )
                except Exception as e:
                    if _is_auth_failure(e):
                        _disconnect()
                        msg = format_mcp_auth_error(e) or str(e)
                        reply = f"{msg}\n\nDisconnected — please reconnect on the Connection tab."
                    else:
                        reply = f"Something went wrong: {e}"
                    mcp_trace = {"context_injected": None, "steps": []}
            st.markdown(reply)

        st.session_state.messages.append(
            {"role": "assistant", "content": reply, "mcp_trace": mcp_trace}
        )
        st.rerun()


def main() -> None:
    st.set_page_config(page_title="Chatbot", page_icon="💬", layout="centered")
    st.title("Chatbot")
    st.caption("Connect to one MCP server, then chat with the agent (API key required).")

    _init_session_state()

    tab_connection, tab_chat = st.tabs(["Connection", "Chat"])
    with tab_connection:
        _connection_tab()
    with tab_chat:
        _chat_tab()


main()
