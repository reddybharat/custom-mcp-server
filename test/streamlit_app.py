"""Streamlit chat UI for the MCP-backed LangChain agent."""

import asyncio
import sys
from pathlib import Path

# Allow `streamlit run test/streamlit_app.py` from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from agent import build_chat_agent


def _message_content(msg) -> str:
    c = getattr(msg, "content", None)
    if c is None:
        return str(msg)
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        parts = []
        for block in c:
            if isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(c)


@st.cache_resource(show_spinner="Connecting to MCP servers and loading agent…")
def get_agent():
    return asyncio.run(build_chat_agent())


def main():
    st.set_page_config(page_title="Chatbot", page_icon="💬", layout="centered")
    st.title("Chatbot")
    st.caption("Chatbot connected with Custom MCP Server, you can ask questions about math and weather.")

    if not st.session_state.get("messages"):
        st.session_state.messages = []

    try:
        agent = get_agent()
    except Exception as e:
        st.error(f"Could not start the agent. Is the MCP server running and is `GROQ_API_KEY` set?\n\n{e}")
        st.stop()

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Ask something (banking, financial services, or general)…"):
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
                    reply = _message_content(result["messages"][-1])
                except Exception as e:
                    reply = f"Something went wrong: {e}"
            st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})


main()
