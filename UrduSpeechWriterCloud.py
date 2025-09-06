import streamlit as st
import requests
import base64
import json
import datetime
import time
from dotenv import load_dotenv
import os
from difflib import ndiff

# ---------- Config ----------
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "gpt-4o-mini"

st.set_page_config(page_title="Urdu Speech Writer", page_icon="🎤")

# Load Google Fonts for Urdu
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

# ---------- Helper Functions ----------
def encode_audio(audio_bytes):
    """Convert audio bytes to base64"""
    return base64.b64encode(audio_bytes).decode("utf-8")

def transcribe_audio_openrouter(audio_bytes, retries=2, timeout_sec=60):
    """Send audio to OpenRouter for transcription"""
    encoded_audio = encode_audio(audio_bytes)
    messages = [
        {"role": "system", "content": "You are a transcription assistant."},
        {"role": "user", "content": [{"type": "input_audio", "input_audio": {"audio": encoded_audio, "format": "audio/webm"}}]}
    ]
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": MODEL, "messages": messages}

    for attempt in range(retries):
        try:
            with st.spinner(f"Transcribing audio… (attempt {attempt+1})"):
                resp = requests.post(BASE_URL, headers=headers, json=payload, timeout=timeout_sec)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            else:
                st.warning(f"API returned status {resp.status_code}: {resp.text}")
        except requests.exceptions.Timeout:
            st.warning("Request timed out. Retrying…")
            time.sleep(2)
    return "❌ Failed to transcribe audio."

def translate_to_urdu(text, retries=2, timeout_sec=60):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Translate the following text into Urdu."},
            {"role": "user", "content": text}
        ]
    }
    for attempt in range(retries):
        try:
            with st.spinner(f"Translating to Urdu… (attempt {attempt+1})"):
                resp = requests.post(BASE_URL, headers=headers, json=payload, timeout=timeout_sec)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.Timeout:
            st.warning("Request timed out. Retrying…")
            time.sleep(2)
    return "❌ Failed to translate."

def proofread_urdu(urdu_text, source_text="", retries=2, timeout_sec=60):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    sys_prompt = (
        "You are an Urdu copyeditor. Correct spelling, spacing, punctuation, "
        "and obvious word errors, but keep the user's meaning. "
        "Return ONLY valid JSON with keys: corrected (string), changes (array of objects with from,to,reason)."
    )
    user_prompt = (
        f"Original Urdu:\n{urdu_text}\n\nReference text:\n{source_text}\n\n"
        "Return JSON like:\n"
        '{"corrected":"...", "changes":[{"from":"غلط","to":"صحیح","reason":"typo"}]}'
    )
    payload = {"model": MODEL, "messages":[{"role":"system","content":sys_prompt},{"role":"user","content":user_prompt}]}

    for attempt in range(retries):
        try:
            with st.spinner(f"Proofreading Urdu… (attempt {attempt+1})"):
                resp = requests.post(BASE_URL, headers=headers, json=payload, timeout=timeout_sec)
            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"]
                try:
                    result = json.loads(text)
                    return result.get("corrected", ""), result.get("changes", [])
                except Exception:
                    return text, []
        except requests.exceptions.Timeout:
            st.warning("Request timed out. Retrying…")
            time.sleep(2)
    return None, []

def diff_text(old: str, new: str) -> str:
    diff = ndiff(old.split(), new.split())
    out = []
    for token in diff:
        if token.startswith("+ "):
            out.append(f"**{token[2:]}**")
        elif token.startswith("- "):
            out.append(f"~~{token[2:]}~~")
        else:
            out.append(token[2:] if token.startswith("  ") else token)
    return " ".join(out)

# ---------- Main ----------
def main():
    if "original_urdu" not in st.session_state:
        st.session_state.original_urdu = ""
    if "urdu_edit" not in st.session_state:
        st.session_state.urdu_edit = ""
    if "last_source" not in st.session_state:
        st.session_state.last_source = ""

    st.title("🎤 Urdu Speech Writer (Cloud Compatible)")

    # ---------- Sidebar ----------
    with st.sidebar:
        st.subheader("Settings")
        urdu_font = st.selectbox(
            "Choose Urdu font",
            ["Noto Nastaliq Urdu", "Jameel Noori Nastaleeq", "Scheherazade", "Alvi Nastaleeq"]
        )

    # ---------- Audio Capture ----------
    audio_data = st.audio_input("Record your voice…")
    if audio_data:
        audio_bytes = audio_data.getbuffer()
        source_text = transcribe_audio_openrouter(audio_bytes)
        if source_text.startswith("❌"):
            st.error(source_text)
        else:
            st.success(f"Recognized: {source_text}")

            if not st.session_state.original_urdu:
                urdu_text = translate_to_urdu(source_text)
                st.session_state.original_urdu = urdu_text
                st.session_state.urdu_edit = urdu_text
                st.session_state.last_source = source_text

                # Append to file
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open("urdu_output.html", "a", encoding="utf-8") as f:
                    f.write(f"<p><strong>Time: {timestamp}</strong></p>{st.session_state.urdu_edit}<hr>")

    # ---------- Editable Text ----------
    st.subheader("📝 Urdu Output")
    st.text_area("Edit Urdu text:", value=st.session_state.urdu_edit, height=180, key="urdu_edit")

    # ---------- Live Font Preview ----------
    st.subheader("📖 Live Preview")
    st.markdown(f"""
    <div style="font-family: '{urdu_font}', serif; font-size: 22px; line-height:1.6; border:1px solid #ddd; padding:10px; border-radius:5px;">
    {st.session_state.urdu_edit}
    </div>
    """, unsafe_allow_html=True)

    # ---------- Replace Words ----------
    st.markdown("---")
    st.subheader("✏️ Replace Words")
    with st.form(key="replace_form"):
        old_word = st.text_input("Word to replace:")
        new_word = st.text_input("Replace with:")
        submit_replace = st.form_submit_button("Replace")
        if submit_replace:
            if old_word.strip() and new_word.strip():
                st.session_state.urdu_edit = st.session_state.urdu_edit.replace(old_word, new_word)
                st.success(f"Replaced '{old_word}' with '{new_word}'.")

    # ---------- Buttons ----------
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("💾 Save Live Preview"):
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            html_content = f"""
            <div style="font-family: '{urdu_font}', serif; font-size:22px; line-height:1.6;">
            <p><strong>Time: {timestamp}</strong></p>
            {st.session_state.urdu_edit}
            </div><hr>
            """
            with open("urdu_output.html", "a", encoding="utf-8") as f:
                f.write(html_content)
            st.success(f"Saved live preview at {timestamp}")

    with col2:
        if st.button("🔎 Proofread Urdu"):
            corrected, changes = proofread_urdu(st.session_state.urdu_edit, st.session_state.last_source)
            if corrected:
                st.markdown("**Corrected Urdu:**")
                st.write(corrected)
                st.markdown("**Diff view:**")
                st.markdown(diff_text(st.session_state.urdu_edit, corrected))
                st.session_state.urdu_edit = corrected

    with col3:
        if st.button("🧹 Clear"):
            st.session_state.original_urdu = ""
            st.session_state.urdu_edit = ""
            st.session_state.last_source = ""
            st.experimental_rerun()

# ---------- Run ----------
if __name__ == "__main__":
    main()
