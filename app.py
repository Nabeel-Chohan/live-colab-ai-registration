import gradio as gr
import json
from datetime import datetime
from openai import OpenAI

# === CONFIGURE OPENAI CLIENT ===
client = OpenAI(api_key="OPENAI_API_KEY")  # <-- replace with your key

# === GLOBAL STATE ===
conversation_history = ""
client_data = {}

# === FUNCTIONS ===
def transcribe(audio_file):
    """Transcribe speech to text using Whisper."""
    with open(audio_file, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="en"
        )
    return transcript.text

def format_data_as_table(data):
    """Formats a dictionary into a fixed-width, text-based table."""
    # Prepare data for display, ensuring consistent keys and handling missing values.
    display_items = [
        ("Name", data.get("name", "N/A")),
        ("Household Members", data.get("household_members", "N/A")),
        ("Address", data.get("address", "N/A")),
        ("Phone", data.get("phone", "N/A")),
        ("Timestamp", data.get("timestamp", "N/A"))
    ]

    # Convert all values to strings for measurement.
    display_items_str = [(str(k), str(v)) for k, v in display_items]

    # Calculate column widths, ensuring they are wide enough for headers.
    key_col_width = max(len(k) for k, v in display_items_str)
    key_col_width = max(key_col_width, len("Field"))

    value_col_width = max(len(v) for k, v in display_items_str)
    value_col_width = max(value_col_width, len("Value"))

    # Build the table string.
    separator = f"+-{'-' * key_col_width}-+-{'-' * value_col_width}-+"
    header = f"| {'Field'.ljust(key_col_width)} | {'Value'.ljust(value_col_width)} |"

    lines = [separator, header, separator]
    for key, value in display_items_str:
        lines.append(f"| {key.ljust(key_col_width)} | {value.ljust(value_col_width)} |")
    lines.append(separator)

    return "\n".join(lines)


def process_input(audio_file):
    global conversation_history, client_data

    # Step 1: Transcribe
    transcript = transcribe(audio_file)

    # Step 2: Ask GPT to extract structured info
    system_prompt = f"""
    You are an assistant that extracts 4 fields: name, household_members, address, phone.
    - If any are missing, ask ONE clarifying question.
    - If all are present, output only valid JSON with those fields.

    CONVERSATION:
    {conversation_history}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcript},
        ],
        temperature=0.1
    )

    reply = response.choices[0].message.content.strip()

    conversation_history += f"\nUser: {transcript}\nAssistant: {reply}"

    # Step 3: Update state or store data
    if reply.startswith("{") and reply.endswith("}"):
        try:
            parsed_data = json.loads(reply)
            # Check if all fields are present before finalizing
            if all(k in parsed_data for k in ["name", "household_members", "address", "phone"]):
                client_data = parsed_data
                client_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except json.JSONDecodeError:
            # The reply looks like JSON but isn't valid.
            # We can either ignore it or ask the user to clarify.
            # For now, we'll just let it be treated as a normal conversational turn.
            pass

    # Step 4: Return conversation so far
    display_text = conversation_history
    if client_data:
        display_text += "\n\n✅ Final extracted data:\n" + format_data_as_table(client_data)
    return display_text

# === GRADIO APP ===
demo = gr.Interface(
    fn=process_input,
    inputs=gr.Audio(sources=["microphone"], type="filepath"),
    outputs="text",
    live=False,
    title="🎤 Voice Registration (Minimal Version)",
    description="Speak the information. The system will transcribe, extract details, and show results here."
)

# Launch in Colab
demo.launch(debug=True, share=False)
