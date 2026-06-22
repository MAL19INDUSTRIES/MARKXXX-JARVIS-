# JARVIS — Usage Guide

This guide is focused on **daily usage** once you’ve installed and started the app.

## Start Jarvis

```bash
python3 main.py
```

If `GEMINI_API_KEY` is set correctly, Jarvis will:
- open the UI
- start microphone audio
- connect to Gemini Live
- listen and respond by voice

## What you can say (practical examples)

### 1) Basic actions
- “Open Chrome”
- “What’s the weather in Paris?”
- “Search the web for …”

### 2) Screen / camera questions
- “What is on my screen?”
- “Look at my camera and tell me what you see”
- “Analyze this screenshot”

### 3) Reminders
- “Set a reminder for tomorrow at 8:30 AM to call Mom”

### 4) Files
When you have a file available via the UI/upload flow, you can ask for:
- “Summarize this PDF”
- “Extract text from this image”
- “Fix and optimize this code”
- “Analyze this CSV”

### 5) Desktop controls
Examples (depending on what your toolset supports):
- “Organize my desktop by type”
- “Clean my downloads folder”
- “Take a screenshot”

## Troubleshooting during usage

### API key issues
If you see:
- `GEMINI_API_KEY environment variable not set`

Fix:
- ensure `.env` exists in the repo root
- set `GEMINI_API_KEY`
- restart Jarvis

### Voice not available
If Jarvis can’t use your selected voice, it will fall back to the default voice (`puck`).

Fix:
- set `GEMINI_VOICE_NAME` to a supported voice name from `main.py`

### If tools fail
Jarvis usually logs errors to the UI log.

Fix:
- check environment permissions (mic, display, etc.)
- ensure any optional dependencies (like Playwright) are installed
- if needed, open an issue with the traceback
