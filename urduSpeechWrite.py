import streamlit as st
import speech_recognition as sr
import requests
import io
from pydub import AudioSegment
from dotenv import load_dotenv
import os
import json
from difflib import ndiff
import time
import datetime

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
            time.sleep(2)
        except Exception as e:
            st.warning(f"API Error: {e}")
            time.sleep(2)
    return "❌ Failed to get translation after retries."

def openrouter_proofread_urdu(urdu_text: str, source_text: str = "", retries=2, timeout_sec=60):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    sys = (
        "You are an Urdu copyeditor. Correct spelling, spacing, punctuation and obvious word errors, "
        "but keep the user's meaning. Return ONLY valid JSON with keys: corrected (string), "
        "changes (array of objects with from,to,reason)."
    )
    user = (
        f"Original Urdu:\n{urdu_text}\n\nReference text:\n{source_text}\n\n"
        "Return JSON like:\n"
        '{"corrected":"...", "changes":[{"from":"غلط","to":"صحیح","reason":"typo"}]}'
    )
    payload = {"model": MODEL, "messages":[{"role":"system","content":sys},{"role":"user","content":user}]}

    for attempt in range(retries):
        try:
            with st.spinner(f"Proofreading Urdu… (attempt {attempt+1})"):
                resp = requests.post(BASE_URL, headers=headers, json=payload, timeout=timeout_sec)
            data = resp.json()
            text = None
            if "choices" in data:
                text = data["choices"][0]["message"]["content"]
            if text:
                try:
                    result = json.loads(text)
                    corrected = result.get("corrected", "").strip()
                    changes = result.get("changes", [])
                    return {"corrected": corrected, "changes": changes}, None
                except Exception:
                    return {"corrected": text.strip(), "changes": []}, None
        except requests.exceptions.Timeout:
            st.warning("Request timed out. Retrying…")
            time.sleep(2)
        except Exception as e:
            st.warning(f"API Error: {e}")
            time.sleep(2)
    return None, "❌ Failed to proofread after retries."

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
    if "last_source" not in st.session_state:
        st.session_state.last_source = ""
    if "urdu_edit" not in st.session_state:
        st.session_state.urdu_edit = ""

    st.title("🎤 Urdu Speech Writer")
    st.caption("Record → transcribe → translate → proofread & replace words → save.")

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

    # ---------- Audio capture ----------
    audio_data = st.audio_input("Tap to record…")
    if audio_data:
        audio_bytes = audio_data.getbuffer()
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
            st.session_state.last_source = source_text

            # Append to file
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                with open("urdu_output.txt", "a", encoding="utf-8") as f:
                    f.write(f"---\nTime: {timestamp}\n")
                    f.write(urdu + "\n")
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

    # ---------- Replace Words Section ----------
    st.markdown("---")
    st.subheader("✏️ Replace Words in Paragraph")
    with st.form(key="replace_form"):
        old_word = st.text_input("Word to replace:")

        # Audio input for replacement
        replace_audio = st.audio_input("🎤 Speak replacement word (optional)")
        new_word = ""
        if replace_audio:
            try:
                audio_bytes = replace_audio.getbuffer()
                audio_seg = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")
                wav_io = io.BytesIO()
                audio_seg.export(wav_io, format="wav")
                wav_io.seek(0)

                recognizer = sr.Recognizer()
                with sr.AudioFile(wav_io) as source:
                    audio_content = recognizer.record(source)
                new_word = recognizer.recognize_google(audio_content, language="ur-PK")
                st.text_input("Replace with:", value=new_word, key="new_word_text")
            except Exception as e:
                st.warning(f"Could not recognize audio: {e}")
                new_word = st.text_input("Replace with:", key="new_word_text")
        else:
            new_word = st.text_input("Replace with:", key="new_word_text")

        submit_replace = st.form_submit_button("Replace Word")
        if submit_replace:
            if old_word.strip() == "" or new_word.strip() == "":
                st.warning("Both fields must be filled.")
            else:
                st.session_state.urdu_edit = st.session_state.urdu_edit.replace(old_word, new_word)
                st.success(f"Replaced '{old_word}' with '{new_word}'!")

    # ---------- Buttons: Save, Proofread, Clear ----------
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("💾 Save to file"):
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
        if st.button("🔎 Proofread & Fix Urdu"):
            if not st.session_state.urdu_edit.strip():
                st.warning("Nothing to proofread.")
            else:
                result, err = openrouter_proofread_urdu(st.session_state.urdu_edit, st.session_state.last_source)
                if err:
                    st.error(err)
                else:
                    corrected = result["corrected"]
                    changes = result.get("changes", [])
                    st.markdown("**Corrected Urdu:**")
                    st.write(corrected)
                    st.markdown("**Changes (diff view):**")
                    st.markdown(diff_text(st.session_state.urdu_edit, corrected))
                    if changes:
                        st.markdown("**Change log:**")
                        for c in changes:
                            frm = c.get("from","")
                            to = c.get("to","")
                            reason = c.get("reason","")
                            st.markdown(f"- `{frm}` → **{to}** — {reason}")
                    if st.button("✔️ Use corrected"):
                        st.session_state.urdu_edit = corrected
                        st.experimental_rerun()
    with col3:
        if st.button("🧹 Clear"):
            st.session_state.original_urdu = ""
            st.session_state.urdu_edit = ""
            st.session_state.last_source = ""
            st.experimental_rerun()

# ---------- Run ----------
if __name__ == "__main__":
    main()
