import json
import io
import re
import subprocess
import sys
import time
from pathlib import Path

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE    = 0.06
    _PYAUTOGUI = True
except ImportError:
    _PYAUTOGUI = False

try:
    import pyperclip
    _PYPERCLIP = True
except ImportError:
    _PYPERCLIP = False

JARVIS_TEXT_FOOTER = "CREATED BY JARVIS"

def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

def _get_os() -> str:
    try:
        cfg = json.loads(
            (_base_dir() / "config" / "api_keys.json").read_text(encoding="utf-8")
        )
        return cfg.get("os_system", "windows").lower()
    except Exception:
        return "windows"


def _get_api_key() -> str:
    try:
        cfg = json.loads(
            (_base_dir() / "config" / "api_keys.json").read_text(encoding="utf-8")
        )
        return cfg.get("gemini_api_key", "").strip()
    except Exception:
        return ""


def _require_pyautogui():
    if not _PYAUTOGUI:
        raise RuntimeError("PyAutoGUI not installed. Run: pip install pyautogui")


def _paste_text(text: str) -> None:
    _require_pyautogui()

    os_name = _get_os()
    paste_hotkey = ("command", "v") if os_name == "mac" else ("ctrl", "v")

    if _PYPERCLIP:
        try:
            pyperclip.copy(text)
            time.sleep(0.15)
            pyautogui.hotkey(*paste_hotkey)
            time.sleep(0.1)
            return
        except Exception as e:
            print(f"[SendMessage] ⚠️ Clipboard paste failed, typing instead: {e}")
    pyautogui.write(text, interval=0.03)


def _type_text_visible(text: str, interval: float = 0.035) -> None:
    """Type user-visible message text instead of pasting it from the clipboard."""
    _require_pyautogui()
    for ch in str(text or ""):
        if ch == "\n":
            pyautogui.hotkey("shift", "enter")
            time.sleep(interval * 2)
            continue
        try:
            pyautogui.write(ch, interval=interval)
        except Exception:
            # Last-resort fallback for characters PyAutoGUI cannot synthesize.
            _paste_text(ch)
        time.sleep(interval)


def _screen_find(description: str, retries: int = 2, delay: float = 0.6) -> tuple[int, int] | None:
    api_key = _get_api_key()
    if not api_key:
        print("[SendMessage] ⚠️ No Gemini key for screen vision.")
        return None

    for attempt in range(max(1, retries)):
        try:
            from google import genai
            from google.genai import types as gtypes

            _require_pyautogui()
            w, h = pyautogui.size()
            img = pyautogui.screenshot()
            buf = io.BytesIO()
            img.save(buf, format="PNG")

            prompt = (
                f"You are controlling a {w}x{h} screen for JARVIS messaging. "
                f"Find this exact UI target: {description}. "
                "Prefer visible text fields, buttons, or list results in the active browser/app. "
                "Return ONLY the center coordinate as x,y. If not visible, return NOT_FOUND."
            )
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=[
                    gtypes.Part.from_bytes(data=buf.getvalue(), mime_type="image/png"),
                    prompt,
                ],
            )
            text = (response.text or "").strip()
            if "NOT_FOUND" not in text.upper():
                match = re.search(r"(\d+)\s*,\s*(\d+)", text)
                if match:
                    return int(match.group(1)), int(match.group(2))
        except Exception as e:
            print(f"[SendMessage] ⚠️ screen_find failed: {e}")
        time.sleep(delay * (attempt + 1))
    return None


def _vision_click(description: str, retries: int = 2, delay: float = 0.6) -> bool:
    coords = _screen_find(description, retries=retries, delay=delay)
    if not coords:
        return False
    pyautogui.click(coords[0], coords[1])
    time.sleep(0.5)
    return True


def _with_jarvis_footer(text: str) -> str:
    message = str(text or "").strip()
    if JARVIS_TEXT_FOOTER.lower() in message.lower():
        return message
    return f"{message}\n\n{JARVIS_TEXT_FOOTER}"


def _clear_and_paste(text: str) -> None:
    _require_pyautogui()
    os_name = _get_os()
    select_all = ("command", "a") if os_name == "mac" else ("ctrl", "a")
    pyautogui.hotkey(*select_all)
    time.sleep(0.1)
    pyautogui.press("delete")
    time.sleep(0.1)
    _paste_text(text)

def _open_app(app_name: str) -> bool:
    _require_pyautogui()
    os_name = _get_os()

    try:
        if os_name == "windows":
            pyautogui.press("win")
            time.sleep(0.5)
            _paste_text(app_name)
            time.sleep(0.6)
            pyautogui.press("enter")
            time.sleep(2.5)
            return True

        elif os_name == "mac":
            result = subprocess.run(
                ["open", "-a", app_name],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                result = subprocess.run(
                    ["open", "-a", f"{app_name}.app"],
                    capture_output=True, text=True, timeout=10,
                )
            time.sleep(2.5)
            return result.returncode == 0

        else: 
            launched = False
            for launcher in [
                ["gtk-launch", app_name.lower()],
                [app_name.lower()],
            ]:
                try:
                    subprocess.Popen(
                        launcher,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    launched = True
                    break
                except FileNotFoundError:
                    continue
            time.sleep(2.5)
            return launched

    except Exception as e:
        print(f"[SendMessage] ⚠️ Could not open {app_name}: {e}")
        return False


def _open_browser_url(url: str) -> bool:
    import webbrowser
    try:
        webbrowser.open(url)
        time.sleep(4.0) 
        return True
    except Exception as e:
        print(f"[SendMessage] ⚠️ Could not open browser: {e}")
        return False

def _search_in_app(query: str) -> None:
    _require_pyautogui()
    os_name = _get_os()
    search_hotkey = ("command", "f") if os_name == "mac" else ("ctrl", "f")

    pyautogui.hotkey(*search_hotkey)
    time.sleep(0.5)
    _clear_and_paste(query)
    time.sleep(1.0)

def _desktop_send(app_name: str, receiver: str, message: str) -> str:
    if not _open_app(app_name):
        return f"Could not open {app_name}."

    time.sleep(1.0)
    _search_in_app(receiver)
    pyautogui.press("enter")
    time.sleep(0.8)

    _type_text_visible(message)
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.3)
    return f"Message sent to {receiver} via {app_name}."


def _send_current_app(receiver: str, message: str) -> str:
    _require_pyautogui()
    _vision_click(
        "message composer text field in the currently open chat or messaging app",
        retries=3,
    )
    _type_text_visible(message)
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.3)
    target = f" to {receiver}" if receiver else ""
    return f"Message sent{target} in the current app."

def _send_whatsapp(receiver: str, message: str) -> str:
    return _desktop_send("WhatsApp", receiver, message)

def _send_telegram(receiver: str, message: str) -> str:
    return _desktop_send("Telegram", receiver, message)

def _send_signal(receiver: str, message: str) -> str:
    return _desktop_send("Signal", receiver, message)


def _send_discord(receiver: str, message: str) -> str:
    return _desktop_send("Discord", receiver, message)


def _send_instagram(receiver: str, message: str) -> str:
    _require_pyautogui()

    if not _open_browser_url("https://www.instagram.com/direct/inbox/"):
        return "Could not open Instagram in browser."

    if not _vision_click("Instagram Direct Messages new message button or compose message button", retries=3):
        if not _open_browser_url("https://www.instagram.com/direct/new/"):
            return "Could not open Instagram new message composer."
        time.sleep(1.0)

    _vision_click("Instagram recipient search field in the New Message dialog", retries=3)
    _paste_text(receiver)
    time.sleep(1.5)

    if not _vision_click(f"Instagram recipient search result for '{receiver}'", retries=4):
        pyautogui.press("down")
        time.sleep(0.3)
        pyautogui.press("enter")
        time.sleep(0.4)

    if not _vision_click("Instagram Chat button or Next button to open the selected direct message", retries=3):
        pyautogui.press("enter")
        time.sleep(1.4)

    if not _vision_click("Instagram direct message text box or message composer input at the bottom of the chat", retries=5):
        for _ in range(6):
            pyautogui.press("tab")
            time.sleep(0.12)

    _type_text_visible(message)
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.3)

    return f"Message sent to {receiver} via Instagram."


def _send_messenger(receiver: str, message: str) -> str:
    _require_pyautogui()

    if not _open_browser_url("https://www.messenger.com/"):
        return "Could not open Messenger in browser."


    _search_in_app(receiver)
    time.sleep(0.5)
    pyautogui.press("down")
    time.sleep(0.3)
    pyautogui.press("enter")
    time.sleep(1.0)

    _type_text_visible(message)
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.3)

    return f"Message sent to {receiver} via Messenger."

_PLATFORM_MAP = [
    ({"current", "active", "focused", "frontmost", "any", "generic"}, _send_current_app),
    ({"whatsapp", "wp", "wapp"},              _send_whatsapp),
    ({"telegram", "tg"},                      _send_telegram),
    ({"instagram", "ig", "insta"},            _send_instagram),
    ({"signal"},                               _send_signal),
    ({"discord"},                              _send_discord),
    ({"messenger", "facebook", "fb"},         _send_messenger),
]


def _resolve_platform(platform_str: str):
    key = platform_str.lower().strip()
    for keywords, handler in _PLATFORM_MAP:
        if any(k in key for k in keywords):
            return handler
    return lambda r, m: _desktop_send(platform_str.strip().title(), r, m)


def send_message(
    parameters: dict,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    params       = parameters or {}
    receiver     = params.get("receiver", "").strip()
    message_text = params.get("message_text", "").strip()
    platform     = params.get("platform", "whatsapp").strip()
    platform_key = platform.lower().strip()

    if not receiver and platform_key not in {"current", "active", "focused", "frontmost", "any", "generic"}:
        return "Please specify a recipient."
    if not message_text:
        return "Please specify the message content."
    if not _PYAUTOGUI:
        return "PyAutoGUI is not installed — cannot control the desktop."

    message_text = _with_jarvis_footer(message_text)
    preview = message_text[:50] + ("…" if len(message_text) > 50 else "")
    print(f"[SendMessage] 📨 {platform} → {receiver}: {preview}")
    if player:
        player.write_log(f"[msg] {platform} → {receiver}")

    try:
        handler = _resolve_platform(platform)
        result  = handler(receiver, message_text)
    except Exception as e:
        result = f"Could not send message: {e}"

    print(f"[SendMessage] {'✅' if 'sent' in result.lower() else '❌'} {result}")
    if player:
        player.write_log(f"[msg] {result}")

    return result
