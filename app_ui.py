import base64
import streamlit as st
import io
import os
import time
import httpx
from audiorecorder import audiorecorder  # Clean browser audio recording component

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# 1. Initialize page and API config
polly_enabled = os.getenv("POLLY_ENABLED", "false").lower() == "true"

# 2. Page Configuration & Styling
st.set_page_config(page_title="MCP Compliance Agent", page_icon="🎙️", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allowed_html=True)

st.title("🎙️ Multimodal MCP Compliance Copilot")
st.caption("Connected to Domain Subsystems via Model Context Protocol | Fallback: Google Gemini")
st.separator()

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "System online. Send a chat message or record an operator voice memo to audit accounts."}
    ]

# 3. Sidebar: Voice Operations Panel
with st.sidebar:
    st.header("🎛️ Voice Control Center")
    st.write("Record an instruction to execute a voice-to-voice check:")
    
    # Render audio recorder widget (Clicks to Start/Stop)
    audio_data = audiorecorder("Click to Record", "Click to Stop Recording")
    
    st.separator()
    st.markdown("### Mock MCP Database State")
    st.info("**Target Account:** ACC-991A\n\n**Subsystem:** Fintech Ledger Server")

# Helper: Transcribe Audio via AWS Transcribe (Mock/Local logic for local testing stability)
def transcribe_audio(audio_bytes):
    # For a fast browser demo, return a mocked transcription.
    st.toast("Processing audio wave frequencies...", icon="⚙️")
    time.sleep(1)
    return "Check account ACC-991A for possible fraud"

# 4. Handle Voice Input Event
if audio_data is not None and len(audio_data) > 0:
    # Extract audio bytes from browser component
    wav_bytes = audio_data.export().read()

    # Process Voice-To-Text
    with st.spinner("Transcribing your audio input..."):
        user_query = transcribe_audio(wav_bytes)

    st.session_state.messages.append({"role": "user", "content": f"🗣️ *(Voice Input)* {user_query}"})

    # Execute backend voice-analyze endpoint
    with st.spinner("Querying backend for voice analysis..."):
        response = httpx.post(
            f"{API_BASE_URL}/voice-analyze",
            json={
                "industry": "fintech",
                "query": user_query,
                "audio_url": "",
            },
            timeout=60.0,
        )

        if response.is_error:
            st.error(f"Backend request failed: {response.status_code} {response.text}")
            full_reply = "Backend analysis failed."
            audio_reply_bytes = None
        else:
            payload = response.json()
            summary_text = payload.get("bedrock_evaluation", {}).get("summary", "No evaluation summary returned.")
            verdict = payload.get("bedrock_evaluation", {}).get("verdict", "UNKNOWN")
            full_reply = f"**[VERDICT: {verdict}]** {summary_text}"
            audio_reply_bytes = None
            if payload.get("speech_audio_base64"):
                audio_reply_bytes = io.BytesIO(base64.b64decode(payload["speech_audio_base64"]))

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_reply,
        "audio": audio_reply_bytes,
    })

    # Prevent the recorder from retriggering on the same data
    audio_data = []

# 5. Render Main Screen Chat Interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "audio" in message and message["audio"] is not None:
            st.audio(message["audio"], format="audio/mp3")

# 6. Handle Regular Text Chat Input
if text_prompt := st.chat_input("Type your compliance query here (e.g., 'Check status of ACC-991A')..."):
    st.session_state.messages.append({"role": "user", "content": text_prompt})
    with st.chat_message("user"):
        st.markdown(text_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            response = httpx.post(
                f"{API_BASE_URL}/analyze",
                json={
                    "industry": "fintech",
                    "query": text_prompt,
                    "audio_url": "",
                },
                timeout=60.0,
            )

            if response.is_error:
                st.error(f"Backend request failed: {response.status_code} {response.text}")
                full_reply = "Backend analysis failed."
                audio_reply_bytes = None
            else:
                payload = response.json()
                summary_text = payload.get("bedrock_evaluation", {}).get("summary", "No evaluation summary returned.")
                verdict = payload.get("bedrock_evaluation", {}).get("verdict", "UNKNOWN")
                full_reply = f"**[VERDICT: {verdict}]** {summary_text}"
                audio_reply_bytes = None
                if payload.get("speech_audio_base64"):
                    audio_reply_bytes = io.BytesIO(base64.b64decode(payload["speech_audio_base64"]))

            st.markdown(full_reply)
            if audio_reply_bytes:
                st.audio(audio_reply_bytes, format="audio/mp3")

    st.session_state.messages.append({"role": "assistant", "content": full_reply, "audio": audio_reply_bytes})