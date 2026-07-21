"""GUI home screen: shows the logged-in player + rating and offers Play/Room,
mirroring the shell menu. Returns "play", "room", or "quit"."""

from __future__ import annotations

import tkinter as tk


def prompt_home_action(username: str, rating: int) -> str:
    result = {"action": "quit"}
    root = tk.Tk()
    root.title("Kung-Fu Chess - Home")

    tk.Label(root, text=f"{username}   (rating {rating})", font=("Arial", 12, "bold")).pack(
        padx=24, pady=(16, 8)
    )

    def choose(action: str) -> None:
        result["action"] = action
        root.destroy()

    buttons = tk.Frame(root)
    buttons.pack(padx=24, pady=(0, 16))
    tk.Button(buttons, text="Play", width=12, command=lambda: choose("play")).pack(side=tk.LEFT, padx=6)
    tk.Button(buttons, text="Room", width=12, command=lambda: choose("room")).pack(side=tk.LEFT, padx=6)

    root.protocol("WM_DELETE_WINDOW", lambda: choose("quit"))
    root.mainloop()
    return result["action"]
