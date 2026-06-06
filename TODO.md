# TODO — JARVIS publication hardening

## Step 0 — Gather
- [x] Confirm hotkey wiring in ui.py (F6 minimize/restore)
- [x] Identify publishing blockers (missing CI, api_keys runtime dependency, platform-specific requirements, setup.py side effects)

## Step 1 — Config safety
- [ ] Ensure runtime uses GEMINI_API_KEY env var first, then keyring, then disk config (optional placeholder)
- [ ] Add/ensure `.env.example` and keep secrets out of repo

## Step 2 — Platform-safe requirements
- [ ] Add environment markers to requirements.txt for Windows-only packages
- [ ] Keep macOS/Linux compatible installs

## Step 3 — Replace setup.py
- [ ] Convert setup.py into standard packaging metadata (no install side effects)
- [ ] Or add pyproject.toml for packaging if preferred

## Step 4 — Add CI
- [ ] Add `.github/workflows/ci.yml` to run:
  - python -m py_compile (all .py)
  - optional secret scanning (basic regex)

## Step 5 — Validate
- [ ] Run py_compile locally
- [ ] Run a minimal import test (no API calls)

