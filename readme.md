# 🎤 Urdu Speech Writer

A browser-based **Urdu Speech Writer** that allows users to:

- Record voice in Urdu, Hindi, or English.
- Transcribe speech to text.
- Translate recognized text into Urdu using AI (OpenRouter).
- Proofread and correct Urdu text.
- Replace words manually (via text or speech input).
- Preview in multiple Urdu fonts.
- Save the live preview or final text to a local file.

---

## **Features**

1. **Speech-to-Text**
   - Uses `SpeechRecognition` to capture voice from the browser.
   - Supports multiple languages (`ur-PK`, `hi-IN`, `en-US`).

2. **Urdu Translation**
   - Translates recognized text into Urdu using OpenRouter API (`gpt-4o-mini` model).
   - Handles retries on timeouts or API errors.

3. **Proofreading**
   - AI-based Urdu proofreading with word/spacing/punctuation corrections.
   - Shows a **diff view** and change logs for easy review.

4. **Live Font Preview**
   - Supports multiple Urdu fonts: `Noto Nastaliq Urdu`, `Jameel Noori Nastaleeq`, `Scheherazade`, `Alvi Nastaleeq`.
   - Preview updates automatically as text is edited.

5. **Word Replacement**
   - Replace specific words in the paragraph.
   - Option to input replacement words via **text** or **speech**.

6. **Save Output**
   - Append live preview in selected font to `urdu_output.html`.
   - Append raw Urdu text to `urdu_output.txt` automatically.

---

## **Installation**

1. **Clone the repository:**

```bash
git clone https://github.com/<your-username>/UrduSpeechWriter.git
cd UrduSpeechWriter
```

2. **Create a virtual environment and activate it:**

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Install FFmpeg** (required for `pydub`):

- **Windows:** Download from [FFmpeg website](https://ffmpeg.org/download.html) and add `ffmpeg.exe` to your system PATH.  
- **Linux/Mac:**  

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

5. **Set API Key** (OpenRouter):

- Create a `.env` file:

```env
OPENROUTER_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
```

> **Note:** Do NOT commit your `.env` to GitHub.

---

## **Run the App Locally**

```bash
streamlit run app.py
```

Open the browser URL provided by Streamlit. You can also access it on mobile if connected to the same network.

---

## **Deploy on Streamlit Cloud**

1. Push your project to GitHub (exclude `.env`):

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/UrduSpeechWriter.git
git push -u origin main
```

2. Go to [Streamlit Cloud](https://streamlit.io/cloud) → **New App** → Select your GitHub repo → Deploy.

3. Add **Secrets** in Streamlit Cloud for your API key:

```
OPENROUTER_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
```

4. Your app is live and can be accessed via a mobile or desktop browser.

---

## **Usage Workflow**

1. Tap **record** → Speak in selected language.  
2. View recognized text and automatic Urdu translation.  
3. Edit text manually if needed.  
4. Use **Replace Words** to substitute specific words (text or speech input).  
5. Preview in selected font.  
6. Click **Save** to append output to local files.  
7. Use **Proofread** to auto-correct Urdu text using AI.  

---

## **Dependencies**

- `streamlit` – Web app interface  
- `SpeechRecognition` – Speech-to-text  
- `pydub` – Audio processing  
- `requests` – API calls  
- `python-dotenv` – Load `.env` API keys  
- `json` / `difflib` – Text diffing and parsing  

---

## **License**

MIT License – feel free to use and modify.

---

## **Screenshots / Demo**

*(Optional: Add screenshots or GIFs of the app in action, showing recording, Urdu translation, font preview, and save options.)*

