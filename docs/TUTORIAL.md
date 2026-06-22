# JARVIS — Step-by-Step Tutorial (Local Gemini Live Assistant)

This tutorial shows how to install, configure, run, and troubleshoot **MARK XXXIX JARVIS** on your machine.

> Assumptions: You have macOS/Linux/Windows basics covered, and you’ll run Python locally.

---

## 1) Prerequisites

- **Python 3.11+** installed
- A **Google Gemini API key**
- (Optional but recommended) `playwright` browsers if you plan to use browser automation tools

Check your Python version:

```bash
python3 --version
```

---

## 2) Create a virtual environment

From the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

---

## 3) Install dependencies

```bash
python -m pip install -r requirements.txt
```

> Note: Some dependencies are platform-specific (Windows-only COM/audio automation). On macOS/Linux these are typically ignored via environment markers.

---

## 4) Install Playwright browsers (if needed)

If you will use features like browser control / web automation:

```bash
python -m playwright install
```

---

## 5) Configure environment variables (do NOT commit secrets)

### 5.1 Create your `.env`

A `.env.example` file was added to the repo. Copy it:

```bash
cp .env.example .env
```

Edit `.env` and set:

- `GEMINI_API_KEY="YOUR_GEMINI_API_KEY"`

Optional settings (recommended only if you know you need them):

- `GEMINI_VOICE_NAME` (example: `puck`)
- Trial limiter:
  - `JARVIS_TRIAL_KEYWORD` (set to any non-empty string)
  - `JARVIS_RUNTIME_SECONDS` (default is `3600` seconds)
- Locked volume requirement:
  - `JARVIS_LOCKED_KEY_SECRET`
  - `JARVIS_LOCKED_VOLUME` (requires `/Volumes/<name>/unlock.key`)

### 5.2 Ensure it is loaded

Jarvis attempts to load environment variables automatically (and will also fall back to existing env vars).

---

## 6) (Optional) Understand voice selection

Supported voices are defined in `main.py` under `SUPPORTED_VOICE_NAMES`.

If you set an unsupported voice, Jarvis will fall back to the default voice (`puck`) and log that it switched.

---

## 7) Run JARVIS

Start the assistant:

```bash
python3 main.py
```

Or with variables set inline (alternative way):

```bash
GEMINI_API_KEY="YOUR_KEY" GEMINI_VOICE_NAME="puck" python3 main.py
```

---

## 8) First run: what you should see

On startup Jarvis typically:

- Launches the GUI (Qt UI)
- Initializes the microphone stream
- Connects to Gemini Live
- Greets you with a startup prompt

If the API key is missing, you’ll get an error like:

- `GEMINI_API_KEY environment variable not set`

Fix by adding it to `.env`.

---

## 9) Using JARVIS (basic workflow)

### 9.1 Speak normally

- Talk to Jarvis as you would with any voice assistant.
- Jarvis will interpret intent and either respond or call an internal tool.

### 9.2 The assistant can control your computer

Examples of commands you can try:

- “Open Chrome”
- “What’s the weather in Istanbul?”
- “Search the web for best noise-cancelling headphones”
- “Take a screenshot and tell me what you see” (invokes screen/camera tool)
- “Set a reminder for tomorrow at 8:30 AM to call Mom”

### 9.3 File interactions

If you upload or drop a file (through the UI), you can command things like:

- “Summarize this PDF”
- “Extract text from this image”
- “Fix and reformat this code file”
- “Analyze this CSV”

Jarvis is designed to call the `file_processor` tool for uploaded files.

---

## 10) Common troubleshooting

### 10.1 `GEMINI_API_KEY environment variable not set`

- Verify `.env` exists in the project root
- Verify `GEMINI_API_KEY` is correctly filled

Restart after changes.

### 10.2 Microphone won’t start

- Check OS microphone permissions for your terminal/app
- Confirm no other app is using the microphone

### 10.3 Browser automation errors

- Install Playwright browsers:

```bash
python -m playwright install
```

- Also ensure required system libraries are installed (often mentioned in Playwright errors).

### 10.4 Voice errors / voice fallback

- The assistant will log a fallback if the requested voice isn’t available for the model.
- Set `GEMINI_VOICE_NAME` to one of the supported voice names.

---

## 11) Advanced: local API (optional)

There is an optional HTTP API server in `api/server.py`.

1) Add `JARVIS_API_KEY` to `.env` (don’t commit it)

2) Start the API server:

```bash
uvicorn api.server:app --host 127.0.0.1 --port 8001
```

3) Call status:

```bash
curl -H "Authorization: Bearer YOUR_PRIVATE_KEY" http://127.0.0.1:8001/status
```

> Keep this on `localhost`.

---

## 12) Publishing safely to GitHub

This repo is already set up to avoid secrets being committed:

- `.env` is ignored
- `config/api_keys.json` is ignored
