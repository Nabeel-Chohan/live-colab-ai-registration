# Voice Registration System (Gradio)

A proof-of-concept app for capturing client registration info via **voice input**. Uses **Gradio** for recording, **Whisper API** for transcription, and **GPT-4o-mini** for structured data extraction.

## ✨ Features

* Voice recording via Gradio
* Accurate speech-to-text (Whisper)
* AI data extraction (Name, Household, Address, Phone)
* Conversational follow-ups for missing info
* Real-time conversation + data table display
* Session persistence across inputs

## 🚀 Setup & Usage

1. **Requirements**: Python, `gradio`, `openai`, and OpenAI API key (with Whisper + GPT-4o-mini access).
2. **Configure API Key** in `app.py`:

   ```python
   client = OpenAI(api_key="your-api-key")
   ```
3. **Install deps**:

   ```bash
   pip install gradio openai
   ```
4. **Run app**:

   ```bash
   python app.py
   ```
5. **Use**: Record voice → system transcribes, extracts data, asks clarifications → final table output.

## 🏗 How It Works

1. Record voice → Gradio
2. Transcribe → Whisper
3. Extract fields → GPT-4o-mini
4. Manage conversation for missing info
5. Display results in a timestamped table

## 📁 Files

```
app.py      # Main app
README.md   # Docs
```

## 🔧 Tech

* Gradio (web UI)
* Whisper API (speech-to-text)
* GPT-4o-mini (NLP)
* JSON + timestamp output

## 💡 Benefits

* Minimal setup (single file)
* Natural, conversational input
* Structured data instantly
* Real-time feedback + session persistence

## 🔒 Security

Keep your API key private (use env vars in production).

---

Do you want me to make this **even shorter (like a quick-start guide)** or keep this balance of brevity + clarity?
