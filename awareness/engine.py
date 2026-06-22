from __future__ import annotations

import os
import time
import threading
import subprocess
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Callable, Optional

try:
    from ui import PopupType
except Exception:
    from enum import Enum
    class PopupType(Enum):
        PRESENCE = "presence"


@dataclass
class AwarenessState:
    current_app: str = ""
    current_project: str = ""
    current_project_path: str = ""
    current_activity: str = "Idle"
    current_goal: str = ""
    active_tool: str = ""
    last_action: str = ""
    git_repo: bool = False
    vscode_active: bool = False
    related_project: bool = False
    recent_events: list[str] = field(default_factory=list)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)


class AwarenessEngine:
    def __init__(
        self,
        popup_scheduler: Callable[[str, PopupType], None],
        check_interval: float = 5.0,
        insight_cooldown: float = 300.0,
    ):
        self.popup_scheduler = popup_scheduler
        self.check_interval = check_interval
        self.insight_cooldown = insight_cooldown
        self.state = AwarenessState()
        self._last_insight_time: dict[str, float] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print("[Awareness] 👁️ Awareness engine started")

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        print("[Awareness] 👁️ Awareness engine stopped")

    def get_state(self) -> AwarenessState:
        with self._lock:
            return AwarenessState(**self.state.to_dict())

    def get_context_for_prompt(self) -> str:
        state = self.get_state()
        lines = [
            "[CURRENT AWARENESS STATE]",
            f"Current app: {state.current_app or 'Unknown'}",
            f"Current project: {state.current_project or 'Unknown'}",
            f"Current activity: {state.current_activity or 'Unknown'}",
            f"Current goal: {state.current_goal or 'None'}",
            f"Active tool: {state.active_tool or 'None'}",
            f"Last action: {state.last_action or 'None'}",
        ]
        if state.recent_events:
            lines.append("Recent events:")
            for event in state.recent_events[-5:]:
                lines.append(f"  - {event}")
        return "\n".join(lines) + "\n"

    def set_goal(self, goal: str) -> None:
        self._update_state(current_goal=goal, current_activity="Working")
        self.record_event(f"Goal updated: {goal}")

    def set_active_tool(self, tool: str, action: str = "") -> None:
        self._update_state(
            active_tool=tool,
            last_action=action,
            current_activity="Executing",
        )
        self.record_event(f"Tool active: {tool}")

    def clear_active_tool(self) -> None:
        self._update_state(active_tool="", current_activity="Idle")

    def record_event(self, event: str) -> None:
        with self._lock:
            timestamp = time.strftime("%H:%M:%S")
            self.state.recent_events.append(f"{timestamp} {event}")
            self.state.recent_events = self.state.recent_events[-20:]
            self.state.updated_at = time.time()

    def _update_state(self, **kwargs) -> None:
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self.state, key):
                    setattr(self.state, key, value)
            self.state.updated_at = time.time()

    def _run_loop(self) -> None:
        while self._running:
            try:
                self._check_and_update_state()
            except Exception as e:
                print(f"[Awareness] ⚠️ Error in awareness loop: {e}")
            time.sleep(self.check_interval)

    def _check_and_update_state(self) -> None:
        git_root = self._get_git_root()
        vscode_active = self._is_vscode_active()
        related_project = self._has_related_project()

        current_project = ""
        current_project_path = ""

        if git_root:
            project_path = Path(git_root).parent
            current_project = project_path.name
            current_project_path = str(project_path)

        current_app = "VS Code" if vscode_active else self._get_frontmost_app()

        self._update_state(
            current_app=current_app,
            current_project=current_project,
            current_project_path=current_project_path,
            git_repo=bool(git_root),
            vscode_active=vscode_active,
            related_project=related_project,
        )

        if git_root:
            self._maybe_surface_insight(
                "git_repo_detected",
                f"Repository detected: {current_project}",
                PopupType.PRESENCE,
            )

        if vscode_active:
            self._maybe_surface_insight(
                "vscode_active",
                "Development environment active.",
                PopupType.PRESENCE,
            )

        if related_project:
            self._maybe_surface_insight(
                "related_project_detected",
                "Related project detected nearby.",
                PopupType.PRESENCE,
            )

    def _get_git_root(self) -> Optional[str]:
        path = os.getcwd()
        while path and path != os.path.dirname(path):
            git_path = os.path.join(path, ".git")
            if os.path.isdir(git_path):
                return git_path
            path = os.path.dirname(path)
        return None

    def _is_vscode_active(self) -> bool:
        try:
            output = subprocess.check_output(
                ["ps", "aux"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            for line in output.splitlines():
                if "Code" in line and "grep" not in line and "awareness" not in line:
                    return True
            return False
        except Exception:
            return False

    def _get_frontmost_app(self) -> str:
        try:
            if os.name == "posix":
                script = (
                    'tell application "System Events" '
                    'to get name of first application process whose frontmost is true'
                )
                return subprocess.check_output(
                    ["osascript", "-e", script],
                    text=True,
                    stderr=subprocess.DEVNULL,
                ).strip()
        except Exception:
            pass
        return ""

    def _has_related_project(self) -> bool:
        cwd = os.getcwd()
        parent = os.path.dirname(cwd)
        if parent == cwd:
            return False

        current_git_root = self._get_git_root()
        parent_git = os.path.join(parent, ".git")

        if os.path.isdir(parent_git):
            if current_git_root is None:
                return True
            try:
                return not os.path.samefile(current_git_root, parent_git)
            except Exception:
                return True

        return False

    def _maybe_surface_insight(self, key: str, insight: str, popup_type: PopupType) -> None:
        now = time.time()
        last_time = self._last_insight_time.get(key, 0)
        if now - last_time >= self.insight_cooldown:
            self.popup_scheduler(insight, popup_type)
            self._last_insight_time[key] = now
            self.record_event(insight)
            print(f"[Awareness] 💡 Surfaced insight: {insight}")


if __name__ == "__main__":
    def dummy_schedule_popup(message: str, popup_type: PopupType) -> None:
        print(f"[Popup] {popup_type.value}: {message}")

    engine = AwarenessEngine(dummy_schedule_popup, check_interval=2.0)
    engine.start()

    try:
        time.sleep(5)
        print("")
        print(engine.get_context_for_prompt())
    finally:
        engine.stop()
