import uuid
from typing import Optional

import boto3
import streamlit as st
from botocore.exceptions import BotoCoreError, ClientError

# -----------------------------
# CONFIG - FILL THESE IN
# -----------------------------
AWS_REGION = "us-east-1"
AGENT_ID = "EBSQ7K8JMU"
AGENT_ALIAS_ID = "BRP3GC5URX"  # replace this

# -----------------------------
# BEDROCK CLIENT
# -----------------------------
client = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)


def invoke_agent(prompt: str, session_id: str) -> str:
    """
    Calls the Bedrock Agent and returns the final text response.
    """
    try:
        response = client.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=prompt,
        )

        parts = []

        completion = response.get("completion")
        if completion:
            for event in completion:
                chunk = event.get("chunk")
                if chunk and "bytes" in chunk:
                    parts.append(chunk["bytes"].decode("utf-8"))

        return "".join(parts).strip() or "No response received from agent."

    except (ClientError, BotoCoreError) as e:
        return f"AWS error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


# -----------------------------
# STREAMLIT UI
# -----------------------------
st.set_page_config(page_title="Global Weather Agent", page_icon="🌦️")
st.title("🌦️ Global Weather Agent")
st.caption("Ask for live weather using your Bedrock Agent")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.subheader("Settings")
    st.write(f"Region: `{AWS_REGION}`")
    st.write(f"Agent ID: `{AGENT_ID}`")
    st.write(f"Session ID: `{st.session_state.session_id}`")

    if st.button("Start New Chat"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
user_prompt = st.chat_input("Ask about weather in any city...")

if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Checking weather..."):
            answer = invoke_agent(user_prompt, st.session_state.session_id)
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})