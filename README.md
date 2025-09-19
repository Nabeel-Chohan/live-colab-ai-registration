# Live AI-Powered Client Registration in Google Colab

An innovative and simple proof-of-concept for non-profits to streamline client registration. This tool uses a live microphone to capture client information and leverages the power of OpenAI's models to intelligently extract and format the data before saving it to a Google Sheet. It is built entirely within a single Google Colab notebook, making it accessible and easy to deploy for organizations with limited technical resources.

## ✨ Features

- **Live Voice Input:** A JavaScript-to-Python bridge enables live audio recording directly from the user's microphone within the notebook.
- **Real-Time Transcription:** Utilizes the highly accurate **OpenAI Whisper API** to transcribe spoken information in real-time, providing immediate visual feedback.
- **AI-Powered Data Extraction:** The **GPT-4o model** is instructed to act as an intelligent form, guiding the conversation and extracting structured data (Name, Household Members, Address, Phone) into a clean JSON format.
- **Interactive & Conversational:** The system asks clarifying questions if information is missing or unclear, creating a natural dialogue flow.
- **Review & Save:** The final, extracted data is displayed for review, and the user has the explicit option to save it to a designated Google Sheet.
- **Zero Backend Setup:** The entire solution runs within a Google Colab notebook, eliminating the need for a dedicated web server or complex deployment.

## 🚀 How to Use

### Prerequisites

1.  A Google account.
2.  An OpenAI API key.
3.  A Google Sheet to store the data, with the following column headers: `Name`, `Household Members`, `Address`, `Phone`.

### Instructions

1.  Open the `registration-notebook.ipynb` file in Google Colab.
2.  Follow the step-by-step instructions within the notebook cells. You will be prompted to:
    * Authenticate with your Google account (for Sheets access).
    * Enter your OpenAI API key.
    * Interact with the live microphone to register a client.
3.  Review the extracted data.
4.  Click the final "Save" button to append the new client's information to your Google Sheet.

## 📁 Repository Structure
