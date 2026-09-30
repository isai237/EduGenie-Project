# EduGenie – Google Gemini Powered Learning Assistant

EduGenie is a beginner-friendly AI learning assistant built with Streamlit and Google Gemini. Ask questions, explore difficult topics step by step, summarize material, prepare exam answers, request examples, or generate practice questions in a conversational interface.

## Features

- Chat interface with conversation history for the current session
- Subject, learning-level, and answer-length controls
- Help with explanations, summaries, exam answers, examples, and practice questions
- Clear Chat button to start a fresh conversation
- Friendly handling for missing API credentials and Gemini errors

## Technologies Used

- Python
- Streamlit
- Google Gemini API through the `google-genai` package

## Installation

1. Clone this repository and open its folder.
2. (Recommended) Create and activate a virtual environment:

	```bash
	python -m venv .venv
	source .venv/bin/activate
	```

	On Windows PowerShell, activate it with `.venv\Scripts\Activate.ps1`.
3. Install the dependencies:

	```bash
	pip install -r requirements.txt
	```

## Configure GEMINI_API_KEY

Create an API key in [Google AI Studio](https://aistudio.google.com/app/apikey), then provide it as the `GEMINI_API_KEY` environment variable. Never commit the key to the repository.

For a local Linux or macOS terminal:

```bash
export GEMINI_API_KEY="your-api-key"
```

For Windows PowerShell:

```powershell
$env:GEMINI_API_KEY="your-api-key"
```

In GitHub Codespaces, add `GEMINI_API_KEY` as a Codespaces secret in your GitHub account or repository settings. Restart the Codespace if needed so the secret is available to its terminal. The application can be opened without a key, but Gemini responses require one.

## Run the Project

```bash
streamlit run app.py
```

Streamlit prints a local URL in the terminal. In GitHub Codespaces, open port `8501` when prompted to view the app in your browser.