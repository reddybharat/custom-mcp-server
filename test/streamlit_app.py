"""Log in to the FastAPI app, then call MCP over Streamable HTTP with a Bearer JWT.

1. ``POST {MCP_SERVER_URL}/auth/token`` with ``username`` and ``password`` (form).
2. MCP URLs ``{MCP_SERVER_URL}/math/mcp`` and ``.../weather/mcp`` with header
   ``Authorization: Bearer <access_token>`` (see ``test/config.build_server_config``).

Run API: ``uvicorn main:app`` from repo root. Run UI: ``streamlit run test/streamlit_app.py``.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv

_REPO = Path(__file__).resolve().parents[1]
load_dotenv(_REPO / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent import agent_reply_text, build_chat_agent  # noqa: E402
from config import build_server_config  # noqa: E402


def mcp_base_url() -> str:
    return os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000").rstrip("/")


def fetch_access_token(username: str, password: str) -> str:
    s = requests.Session()
    s.trust_env = False
    r = s.post(
        f"{mcp_base_url()}/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=(5, 20),
    )
    r.raise_for_status()
    return str(r.json()["access_token"])


@st.cache_resource
def chat_agent(token: str):
    return asyncio.run(build_chat_agent(access_token=token))


def main() -> None:
    st.set_page_config(page_title="Chatbot", page_icon="💬", layout="centered")
    st.title("Chatbot")
    st.caption("Custom MCP Server — math and weather tools (Bearer JWT required).")

    if "token" not in st.session_state:
        st.session_state.token = None
    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.caption(f"Server: `{mcp_base_url()}`")

    env_tok = (os.getenv("MCP_BEARER_TOKEN") or "").strip()
    if env_tok and not st.session_state.token:
        st.session_state.token = env_tok
        chat_agent.clear()

    if not st.session_state.token:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Log in"):
            try:
                st.session_state.token = fetch_access_token(u, p)
                st.session_state.messages = []
                chat_agent.clear()
                st.rerun()
            except Exception as e:
                st.error(f"{type(e).__name__}: {e}")
        st.stop()

    if st.button("Log out"):
        st.session_state.token = None
        st.session_state.messages = []
        chat_agent.clear()
        st.rerun()

    try:
        agent = chat_agent(st.session_state.token)
    except Exception as e:
        st.error(f"Could not start the agent. Is the MCP server running, JWT_SECRET set, and GROQ_API_KEY set?\n\n{e}")
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
                    result = asyncio.run(agent.ainvoke(payload))
                    reply = agent_reply_text(result)
                except Exception as e:
                    reply = f"Something went wrong: {e}"
            st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()


main()
