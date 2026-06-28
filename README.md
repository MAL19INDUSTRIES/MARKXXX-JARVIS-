# JARVIS

Local Gemini Live desktop assistant with a PyQt6 interface, voice interaction, detachable panels, and optional browser, file, screen, and messaging tools.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
cp .env.example .env
python3 main.py
```

Set `GEMINI_API_KEY` in `.env` before launch. Optional settings such as voice and local API keys are documented in `.env.example`.

## Documentation

- [Usage guide](docs/USAGE.md)
- [Tutorial](docs/TUTORIAL.md)
- [Contribution notes](CONTRIBUTING.md)

## Configuration files

Template files are included for local setup:

- `.env.example`
- `config/api_keys.example.json`
- `config/layout_settings.example.json`
- `config/ui_settings.example.json`
- `memory/long_term.example.json`
- `memory/task_history.example.json`

## Publishing checklist

- Keep `.env` and local secret files out of git.
- Do not commit `memory/long_term.json` or `config/api_keys.json`.
- Run `python3 -m py_compile main.py ui.py` before tagging a release.

## License

MIT License, see [LICENSE](LICENSE).
