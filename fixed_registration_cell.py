# ==============================================================================
#                 Single-Cell Voice-Powered Registration System - FIXED
# ==============================================================================

# === 1. INSTALL & IMPORT LIBRARIES ===
# Install ffmpeg for audio conversion, then Python libraries
print("🔧 Installing dependencies...")
!apt-get -y update && apt-get -y install ffmpeg
!pip install openai gspread google-auth-oauthlib pydub -q

import json
import base64
import os
import io
import tempfile
from datetime import datetime

import gspread
from google.colab import auth, userdata, output
from google.auth import default
from openai import OpenAI
from IPython.display import HTML, display, clear_output, Javascript
from pydub import AudioSegment

print("✅ Libraries installed and imported successfully.")

# === 2. CONFIGURE SECRETS & AUTHENTICATE ===
print("\n🔐 Configuring access to services...")
try:
    # Configure OpenAI Client
    OPENAI_API_KEY = userdata.get('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key not found in Colab secrets. Please add it via the '🔑' icon on the left.")
    client = OpenAI(api_key=OPENAI_API_KEY)
    print("✅ OpenAI client configured.")

    # Authenticate Google User & Configure Google Sheets Client
    # Added drive.readonly scope which is required for opening sheets by URL
    auth.authenticate_user()
    creds, _ = default(scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.readonly'])
    gc = gspread.authorize(creds)
    print("✅ Google authentication successful.")

    # Open the Google Sheet
    SHEET_URL = userdata.get('SHEET_URL')
    if not SHEET_URL:
        raise ValueError("Google Sheet URL not found in Colab secrets. Please add it.")
    sheet = gc.open_by_url(SHEET_URL).sheet1
    print(f"✅ Connected to Google Sheet: '{sheet.title}'")

    # Verify or set sheet headers, now including Timestamp
    expected_headers = ['Name', 'Household Members', 'Address', 'Phone', 'Timestamp']
    headers = sheet.row_values(1)
    if headers != expected_headers:
        sheet.update('A1:E1', [expected_headers])
        print("📝 Sheet headers have been set to: Name, Household Members, Address, Phone, Timestamp")

except Exception as e:
    print(f"❌ CONFIGURATION ERROR: {e}")
    print("Please check your secrets (OpenAI key, Sheet URL) and ensure the sheet is shared with the service account email from the auth step.")
    raise

# === 3. DEFINE GLOBAL VARIABLES ===
conversation_history = ""
client_data = {}

# === 4. CORE AI & AUDIO PROCESSING FUNCTIONS ===
def transcribe_audio(base64_audio_data):
    """Decodes, converts from webm to wav, and transcribes audio."""
    try:
        # Decode the base64 string to bytes
        audio_bytes = base64.b64decode(base64_audio_data)

        # Load webm audio data from bytes using pydub
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="webm")

        # Export as WAV to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav_file:
            audio_segment.export(temp_wav_file.name, format="wav")
            temp_file_path = temp_wav_file.name

        # Transcribe using Whisper
        with open(temp_file_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )

        os.unlink(temp_file_path) # Clean up the temp file
        return transcript.text
    except Exception as e:
        print(f"Error during transcription: {e}")
        return None

def extract_client_data(transcript, history):
    """Uses GPT-4o to extract client details or ask a clarifying question."""
    system_prompt = """
    You are an intelligent form-filling assistant for a non-profit. Your goal is to extract four pieces of information from the user: Name, Household Members (as an integer), Address, and Phone number.

    - Analyze the user's input based on the conversation history.
    - If any information is missing or unclear, ask a single, direct question to get the missing detail. Your response should be just the question itself, not a JSON object.
    - Once all four pieces of information have been clearly gathered, respond ONLY with a single, complete JSON object. Do not include any other text, formatting, or markdown.

    Example of a final, complete JSON output:
    {"name": "Jane Doe", "household_members": 3, "address": "123 Main St, Anytown, USA", "phone": "555-123-4567"}

    CONVERSATION HISTORY:
    """ + history

    try:
        response = client.chat.completions.create(
            model="gpt-4o", # Using the faster and more cost-effective gpt-4o
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcript}
            ],
            temperature=0.1
        )
        response_text = response.choices[0].message.content.strip()

        # Check if the response is the final JSON object
        if response_text.startswith('{') and response_text.endswith('}'):
            return json.loads(response_text)
        else:
            return {"question": response_text}

    except Exception as e:
        print(f"Error processing with GPT: {e}")
        return {"question": "I'm having a little trouble. Could you please repeat that?"}

# === 5. USER INTERFACE & DISPLAY FUNCTIONS ===
def create_audio_recorder_ui():
    """Generates and displays the HTML/JavaScript audio recording widget."""
    recorder_html = """
    <div style="border: 2px solid #4CAF50; border-radius: 12px; padding: 20px; text-align: center; background-color: #f9f9f9; font-family: sans-serif;">
        <h2 style="color: #333;">🎤 Voice Client Registration</h2>
        <p id="assistant_prompt" style="color: #555; font-size: 1.1em; min-height: 25px; font-weight: bold;">
            Click the button and state the client's information.
        </p>
        <button id="recordBtn" style="background-color: #4CAF50; color: white; padding: 15px 30px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; transition: background-color 0.3s;">
            🎤 Start Recording
        </button>
        <div id="status" style="margin-top: 15px; font-weight: bold; color: #E53935;"></div>
        <audio id="audioPlayback" controls style="width: 100%; margin-top: 20px; display: none;"></audio>
    </div>

    <script>
    let mediaRecorder;
    let audioChunks = [];
    const recordBtn = document.getElementById('recordBtn');
    const statusDiv = document.getElementById('status');

    recordBtn.onclick = async () => {
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
            recordBtn.style.backgroundColor = '#FFB300';
            recordBtn.textContent = '🔄 Processing...';
            recordBtn.disabled = true;
            statusDiv.textContent = '';
        } else {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
                audioChunks = [];
                mediaRecorder.ondataavailable = e => audioChunks.push(e.data);

                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    const reader = new FileReader();
                    reader.onloadend = () => {
                        const base64Audio = reader.result.split(',')[1];
                        google.colab.kernel.invokeFunction('handle_audio_submission', [base64Audio], {});
                    };
                    reader.readAsDataURL(audioBlob);
                    document.getElementById('audioPlayback').src = URL.createObjectURL(audioBlob);
                    document.getElementById('audioPlayback').style.display = 'block';
                    stream.getTracks().forEach(track => track.stop());
                };

                mediaRecorder.start();
                recordBtn.style.backgroundColor = '#E53935';
                recordBtn.textContent = '⏹️ Stop Recording';
                statusDiv.textContent = '🔴 Recording...';
            } catch (err) {
                statusDiv.textContent = "Error: Microphone access denied.";
                console.error("Microphone access error:", err);
            }
        }
    };
    </script>
    """
    display(HTML(recorder_html))

def display_final_review(data):
    """Shows the extracted data and buttons to save or start over."""
    review_html = """
    <div style="border: 2px solid #1E88E5; border-radius: 12px; padding: 20px; font-family: sans-serif; background-color: #f0f7ff;">
        <h3>✅ Please Review Client Information</h3>
        <pre style="background-color: #e3f2fd; padding: 10px; border-radius: 5px; white-space: pre-wrap;">{pretty_data}</pre>
        <button id="saveBtn" onclick="google.colab.kernel.invokeFunction('save_data_to_sheet', [], {{}})" style="background-color: #43A047; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">💾 Save to Sheet</button>
        <button id="resetBtn" onclick="google.colab.kernel.invokeFunction('reset_session_and_ui', [], {{}})" style="background-color: #757575; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">🔄 Register Another Client</button>
        <div id="saveStatus" style="margin-top: 15px; font-weight: bold;"></div>
    </div>
    """.format(pretty_data=json.dumps(data, indent=2))
    display(HTML(review_html))

# === 6. PYTHON CALLBACKS (Registered functions called from JavaScript) ===
@output.register_callback('handle_audio_submission')
def handle_audio_submission(base64_audio):
    global conversation_history, client_data

    clear_output(wait=True)
    print("🎤 Audio received. Transcribing...")

    transcript = transcribe_audio(base64_audio)
    if not transcript:
        print("❌ Transcription failed. Please try recording again.")
        launch_app(prompt="I couldn't hear that. Please try again.")
        return

    print(f"📝 You said: \"{transcript}\"")
    print("🧠 Thinking...")

    conversation_history += f"\nUser: {transcript}"
    result = extract_client_data(transcript, conversation_history)

    if "question" in result:
        assistant_question = result["question"]
        conversation_history += f"\nAssistant: {assistant_question}"
        launch_app(prompt=assistant_question)
    else:
        client_data = result
        display_final_review(client_data)

@output.register_callback('save_data_to_sheet')
def save_data_to_sheet():
    global client_data
    try:
        row_to_insert = [
            client_data.get('name', 'N/A'),
            client_data.get('household_members', 'N/A'),
            client_data.get('address', 'N/A'),
            client_data.get('phone', 'N/A'),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ]

        sheet.append_row(row_to_insert, value_input_option='USER_ENTERED')

        # Provide feedback in the UI using JavaScript
        js_feedback = "document.getElementById('saveStatus').textContent = '✅ Data successfully saved!'; document.getElementById('saveBtn').disabled = true; document.getElementById('saveBtn').style.backgroundColor = '#9E9E9E';"
        display(Javascript(js_feedback))

    except Exception as e:
        error_msg = f"❌ Error saving to sheet: {e}"
        print(error_msg)
        display(Javascript(f"document.getElementById('saveStatus').textContent = '{error_msg}';"))

@output.register_callback('reset_session_and_ui')
def reset_session_and_ui():
    global conversation_history, client_data
    conversation_history = ""
    client_data = {}
    clear_output(wait=True)
    print("🔄 Session reset. Ready for new client registration.")
    launch_app()

# === 7. LAUNCH THE APPLICATION ===
def launch_app(prompt="Hello! I'm here to help with registration. Please tell me the client's full name to start."):
    """Clears previous output and displays the main UI with a prompt."""
    create_audio_recorder_ui()
    # Use json.dumps to safely handle quotes and special characters in the prompt
    display(Javascript(f"document.getElementById('assistant_prompt').textContent = {json.dumps(prompt)}"))

# Initial launch
print("\n🚀 Application is ready. Please use the interface below.")
launch_app()
