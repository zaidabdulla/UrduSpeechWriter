import streamlit as st
import requests
import io
from pydub import AudioSegment
import os
import json
import datetime
from difflib import ndiff
from dotenv import load_dotenv
import speech_recognition as sr

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
def openrouter_translate_to_urdu(text: str, retries=2, timeout_sec=60) -> str:
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Translate the following text into Urdu."},
            {"role": "user", "content": text},
        ],
    }
    for attempt in range(retries):
        try:
            with st.spinner(f"Translating to Urdu… (attempt {attempt+1})"):
                response = requests.post(BASE_URL, headers=headers, json=payload, timeout=timeout_sec)
            data = response.json()
            if "choices" in data:
                return data["choices"][0]["message"]["content"].strip()
        except requests.exceptions.Timeout:
            st.warning("Request timed out. Retrying…")
        except Exception as e:
            st.warning(f"API Error: {e}")
    return "❌ Failed to get translation after retries."

def diff_text(old: str, new: str) -> str:
    diff = ndiff(old.split(), new.split())
    out = []
    for token in diff:
        if token.startswith("+ "):
            out.append(f"**{token[2:]}**")
        elif token.startswith("- "):
            out.append(f"~~{token[2:]}~~")
        elif token.startswith("? "):
            continue
        else:
            out.append(token[2:])
    return " ".join(out)

# ---------- Main Function ----------
def main():
    # Session state initialization
    if "original_urdu" not in st.session_state:
        st.session_state.original_urdu = ""
    if "urdu_edit" not in st.session_state:
        st.session_state.urdu_edit = ""

    st.title("🎤 Urdu Speech Writer")
    st.caption("Upload → transcribe → translate → edit → replace → save.")

    # ---------- Sidebar Settings ----------
    with st.sidebar:
        st.subheader("Settings")
        # Speech language selection
        speech_lang = st.selectbox(
            "Speech language (for recognition)",
            [("Urdu (Pakistan)", "ur-PK"), ("Hindi (India)", "hi-IN"), ("English (US)", "en-US")],
            index=0,
            format_func=lambda x: x[0]
        )[1]

        # Urdu font selection
        urdu_font = st.selectbox(
            "Choose Urdu font",
            ["Noto Nastaliq Urdu", "Jameel Noori Nastaleeq", "Scheherazade", "Alvi Nastaleeq"]
        )

    # ---------- Audio Upload ----------
    audio_file = st.file_uploader("Upload your recorded audio (wav/webm):", type=["wav", "webm"])
    if audio_file:
        audio_bytes = audio_file.read()
        try:
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")
        except:
            try:
                audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="webm")
            except Exception as e:
                st.error(f"❌ Could not decode audio: {e}")
                st.stop()

        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        wav_io.seek(0)

        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(wav_io) as source:
                audio_content = recognizer.record(source)
            source_text = recognizer.recognize_google(audio_content, language=speech_lang)
            st.success(f"Recognized ({speech_lang}): {source_text}")
        except Exception as e:
            st.error(f"❌ Speech Recognition Error: {e}")
            st.stop()

        # Translate once
        if not st.session_state.original_urdu:
            urdu = openrouter_translate_to_urdu(source_text)
            st.session_state.original_urdu = urdu
            st.session_state.urdu_edit = urdu

            # Append to file
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                with open("urdu_output.html", "a", encoding="utf-8") as f:
                    f.write(f"<div><strong>Time: {timestamp}</strong></div>\n")
                    f.write(f"<div>{urdu}</div>\n<hr>\n")
                st.info(f"Saved speech automatically at {timestamp}")
            except Exception as e:
                st.warning(f"Could not save automatically: {e}")

    # ---------- Editable Urdu text ----------
    st.subheader("📝 Urdu Output")
    st.text_area("Edit Urdu text here:", value=st.session_state.urdu_edit, height=180, key="urdu_edit")

    # ---------- Live Font Preview ----------
    st.subheader("📖 Live Preview in Selected Font")
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
        submit_replace = st.form_submit_button("Replace Word")
        if submit_replace:
            if old_word.strip() == "" or new_word.strip() == "":
                st.warning("Both fields must be filled.")
            else:
                st.session_state.urdu_edit = st.session_state.urdu_edit.replace(old_word, new_word)
                st.success(f"Replaced '{old_word}' with '{new_word}'!")

    # ---------- Save and Clear ----------
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("💾 Save Live Preview"):
            try:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                html_content = f"""
                <div style="font-family: '{urdu_font}', serif; font-size:22px; line-height:1.6;">
                <p><strong>Time: {timestamp}</strong></p>
                {st.session_state.urdu_edit}
                </div>
                <hr>
                """
                with open("urdu_output.html", "a", encoding="utf-8") as f:
                    f.write(html_content)
                st.success(f"Live preview appended to urdu_output.html at {timestamp}")
            except Exception as e:
                st.warning(f"Could not save: {e}")

    with col2:
        if st.button("🧹 Clear All"):
            st.session_state.original_urdu = ""
            st.session_state.urdu_edit = ""
            st.experimental_rerun()

# ---------- Run ----------
if __name__ == "__main__":
    main()
