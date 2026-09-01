"""Streamlit chat UI for the MCP agent.

MCP URLs ``{MCP_SERVER_URL}/math/mcp`` and ``.../weather/mcp`` with header
``X-API-Key`` (see ``client.config.build_server_config``).

Run API: ``uvicorn main:app`` from repo root. Run UI: ``streamlit run app.py``.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from client.agent import (
    agent_reply_text,
    ainvoke_with_selective_mcp,
    build_chat_agent,
    format_mcp_auth_error,
)
from client.config import mcp_server_url

_REPO = Path(__file__).resolve().parent
load_dotenv(_REPO / ".env")


@st.cache_resource
def chat_agent(api_key: str):
    return asyncio.run(build_chat_agent(api_key=api_key))


def _is_auth_failure(exc: Exception) -> bool:
    return format_mcp_auth_error(exc) is not None


def main() -> None:
    st.set_page_config(page_title="Chatbot", page_icon="💬", layout="centered")
    st.title("Chatbot")
    st.caption("Custom MCP Server — math and weather tools (API key required).")

    if "api_key" not in st.session_state:
        st.session_state.api_key = None
    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.caption(f"Server: `{mcp_server_url()}`")

    env_key = (os.getenv("MCP_API_KEY") or "").strip()
    if env_key and not st.session_state.api_key:
        st.session_state.api_key = env_key
        chat_agent.clear()

    if not st.session_state.api_key:
        key_input = st.text_input("API Key", type="password", value=env_key or "")
        if st.button("Connect"):
            entered = (key_input or "").strip()
            if not entered:
                st.error("Enter an API key.")
            else:
                try:
                    chat_agent(entered)
                    st.session_state.api_key = entered
                    st.session_state.messages = []
                    chat_agent.clear()
                    st.rerun()
                except Exception as e:
                    msg = format_mcp_auth_error(e) or f"{type(e).__name__}: {e}"
                    st.error(msg)
        st.stop()

    if st.button("Disconnect"):
        st.session_state.api_key = None
        st.session_state.messages = []
        chat_agent.clear()
        st.rerun()

    try:
        bundle = chat_agent(st.session_state.api_key)
    except Exception as e:
        if _is_auth_failure(e):
            st.session_state.api_key = None
            st.session_state.messages = []
            chat_agent.clear()
            msg = format_mcp_auth_error(e) or str(e)
            st.error(f"{msg}\n\nPlease connect again with a valid API key.")
            st.stop()
        st.error(
            f"Could not start the agent. Is the MCP server running, MCP_API_KEY set on the server, "
            f"and GROQ_API_KEY set?\n\n{e}"
        )
        st.stop()

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Ask something about math or weather…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    payload = {
                        "messages": [
                            {"role": x["role"], "content": x["content"]}
                            for x in st.session_state.messages
                        ]
                    }
                    result = asyncio.run(ainvoke_with_selective_mcp(bundle, payload["messages"]))
                    reply = agent_reply_text(result)
                except Exception as e:
                    if _is_auth_failure(e):
                        st.session_state.api_key = None
                        st.session_state.messages = []
                        chat_agent.clear()
                        msg = format_mcp_auth_error(e) or str(e)
                        reply = f"{msg}\n\nDisconnected — please reconnect with a valid API key."
                    else:
                        reply = f"Something went wrong: {e}"
            st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()


main()
