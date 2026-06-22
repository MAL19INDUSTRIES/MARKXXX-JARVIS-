---
name: awareness-engine-enhanced
description: Enhanced awareness engine with VS Code and related project detection
metadata:
  type: project
---

Added two new contextual checks to the awareness engine in awareness/engine.py:

1. VS Code active detection: Checks for running "Code" process (excluding grep and awareness engine itself) and surfaces "Development agent activated." insight via PRESENCE popup.

2. Related project detection: Checks parent directory for a .git folder that is not the same as the current repository's .git (if any) and surfaces "Related project detected." insight via PRESENCE popup.

Both insights use the same 5-minute cooldown as the existing git repository detection to prevent spam. The insights are designed to be subtle, contextual presence events that reinforce JARVIS's awareness of the user's environment without being intrusive.

Related to: [[awareness-engine-initial]]
See also: [[presence-events-list]] for planned additional insights.
**Why:** User feedback emphasized that behavior (presence/awareness) is more important than UI polish, requesting contextual insights that make JARVIS feel alive by showing it's paying attention to the user's workflow.
**How to apply:** The awareness engine runs in the background, checking context every 5 seconds. New insights are surfaced via the existing popup system when appropriate conditions are met and cooldown has elapsed.