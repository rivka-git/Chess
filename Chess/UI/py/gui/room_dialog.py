"""GUI popup for the Room flow: a text box plus Create/Join/Cancel buttons,
matching the CTD26 home screen mockup. Login and the Play/Room choice stay
console-only (see console/login_prompt.py); this is the one home-screen
interaction the presentation depicts as a GUI dialog."""

from __future__ import annotations

import tkinter as tk


def prompt_room_action() -> tuple[str, str] | None:
    """Shows the Room dialog. Returns (action, room_id) where action is
    "create" or "join", or None if the user cancelled."""
    result: dict = {}
    root = tk.Tk()
    root.title("Room")

    tk.Label(root, text="room name").pack(padx=10, pady=(10, 0))
    entry = tk.Entry(root)
    entry.pack(padx=10, pady=(0, 10))
    entry.focus_set()

    def choose(action: str) -> None:
        result["action"] = action
        result["room_id"] = entry.get().strip()
        root.destroy()

    buttons = tk.Frame(root)
    buttons.pack(pady=(0, 10))
    tk.Button(buttons, text="Create", command=lambda: choose("create")).pack(side=tk.LEFT, padx=5)
    tk.Button(buttons, text="Join", command=lambda: choose("join")).pack(side=tk.LEFT, padx=5)
    tk.Button(buttons, text="Cancel", command=lambda: choose("cancel")).pack(side=tk.LEFT, padx=5)

    root.mainloop()

    if result.get("action") in (None, "cancel"):
        return None
    return result["action"], result["room_id"]
