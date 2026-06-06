# Jarvis — Local Gemini Live Assistant

This repository contains a desktop assistant that connects to Google Gemini Live for realtime audio-powered interaction.

## Docs
- **Step-by-step tutorial:** `README/TUTORIAL.md`
- **Daily usage guide:** `README/USAGE.md`

For backward compatibility, the remainder of this file still contains the full setup tutorial.



Table of contents
- Prerequisites
- Setup (virtualenv + deps)
- Playwright browsers
- Configuration (API key & voice)
- Run (quick and advanced)
- Troubleshooting
- Preparing for GitHub (security checklist)
- CI and testing
- Next steps

---

Prerequisites
- Python 3.11+ installed and available as `python3`.
- A Gemini API key (kept secret).

1) Project location
--------------------
Place or clone the project in a folder you control. Example using home Downloads:

```bash
cd ~/Downloads
# If cloned: git clone git@github.com:youruser/yourrepo.git 'Mark-XXXIX-main 3'
cd 'Mark-XXXIX-main 3'
```

2) Create a virtual environment and install dependencies
-------------------------------------------------------
Use a virtual environment to avoid polluting system packages.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

3) Install Playwright browsers (if you will use browser automation)
-----------------------------------------------------------------

```bash
python -m playwright install
```

4) Configuration: API key and voice
----------------------------------
Do NOT commit secrets. Use the provided `.env.example` to create a `.env` file, or export variables in your shell.

Create `.env` from the example and edit:

```bash
cp .env.example .env
# then open .env and set GEMINI_API_KEY
```


Or export variables for a session:

```bash
export GEMINI_API_KEY="YOUR_KEY"
export GEMINI_VOICE_NAME="puck"   # optional; change to one of the supported voices
```

The supported voices are declared in `main.py` under `SUPPORTED_VOICE_NAMES`. If you select an unsupported voice, Jarvis will fall back to the default voice.

5) Quick run (single command)
------------------------------
Replace `YOUR_KEY` with your real Gemini API key:

```bash
GEMINI_API_KEY="YOUR_KEY" GEMINI_VOICE_NAME="puck" python3 main.py
```

6) Running in background and logs
---------------------------------
Background run with log file capture:

```bash
nohup GEMINI_API_KEY="YOUR_KEY" python3 main.py > jarvis.log 2>&1 &
```

Stop the process:

```bash
pkill -f "python3 main.py"
# or kill <PID> after ps aux | grep main.py
```

View logs:

```bash
tail -f jarvis.log
```

7) Development checks
---------------------
- Check `main.py` syntax:

```bash
python3 -m py_compile main.py
```

- Run linters or tests (add `pytest` / `flake8` to the project and CI later).

8) Troubleshooting (common issues)
----------------------------------
- "GEMINI_API_KEY environment variable not set": set the key in `.env` or export it.
- Unsupported voice (e.g., `capella`): Jarvis detects this and falls back to the default voice; change the UI selection or set `GEMINI_VOICE_NAME` to a supported voice.
- Websocket closed with `1000 None`: indicates a normal close; the app currently reconnects automatically — edit reconnect logic in `main.py` if desired.
- Playwright browser errors: run `python -m playwright install` and ensure required system libraries are installed.

For any unexpected tracebacks, copy the console output and open an issue including the traceback and your environment details.

9) Preparing for GitHub (security checklist)
------------------------------------------
Before pushing to a public repo:

1. Do NOT commit secrets.
2. Do not commit `.env`. The repo includes `.env.example` and `.gitignore` entries for `.env` and `config/api_keys.json`. (Even though `config/api_keys.json` is ignored, the app should work with `GEMINI_API_KEY` env var or OS keychain.)
3. If secrets were committed previously, remove them from history using `git filter-repo` or `git filter-branch` and rotate those keys.
4. Add `LICENSE` and `CONTRIBUTING.md` (already included).

Create a new remote and push:

```bash
git init
git add .
git commit -m "Prepare project for release"
git remote add origin git@github.com:youruser/yourrepo.git
git branch -M main
git push -u origin main
```

10) CI and testing
------------------
A minimal CI workflow is included in `.github/workflows/ci.yml`. It installs dependencies and checks Python syntax. Add linters and unit tests for better safety.

11) Next recommended steps
-------------------------
- Run the app locally and verify the startup greeting and voice behavior.
- Consider pinning exact dependency versions: create a pinned requirements file after verifying installs:

```bash
pip freeze > pinned-requirements.txt
```

- Add automated tests for core flows before publishing widely.

12) Local Status API and access control
--------------------------------------
An optional local HTTP API is included to inspect Jarvis' status and recent logs.

Setup:

1. Add a private API key to your `.env` (do NOT commit this):

```text
JARVIS_API_KEY=your_secret_here
```

2. Start the API server (bind to localhost):

```bash
uvicorn api.server:app --host 127.0.0.1 --port 8001
```

3. Query the status using your API key:

```bash
curl -H "Authorization: Bearer your_secret_here" http://127.0.0.1:8001/status
```

Security notes:
- The server validates `JARVIS_API_KEY` and accepts the key via `Authorization: Bearer <key>` or `X-API-KEY` headers.
- Requests are restricted to `localhost` by default; do not expose the API publicly. If you need remote access, use an SSH tunnel to forward the port.

Endpoints:
- `GET /status` — returns JSON status written by the main app.
- `GET /logs?lines=200` — returns the last `lines` lines from `jarvis.log` (defaults to 200).
- `POST /clear_status` — clears the saved status file.

---

If you'd like, I can (A) generate a random `JARVIS_API_KEY` for you and add it to `.env` (not committed), (B) start the API server for a short demo, or (C) configure the app to automatically start the API when Jarvis launches. Which would you like?
