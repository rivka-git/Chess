"""GUI login screen (the second, optional login path alongside the shell one).
A window with username + password fields and a Login button."""

from __future__ import annotations

import tkinter as tk


def prompt_login() -> tuple[str, str] | None:
    """Returns (username, password), or None if the window was closed without
    entering a username."""
    result: dict = {}
    root = tk.Tk()
    root.title("Kung-Fu Chess - Login")

    tk.Label(root, text="Username").grid(row=0, column=0, padx=8, pady=6, sticky="e")
    username = tk.Entry(root)
    username.grid(row=0, column=1, padx=8, pady=6)

    tk.Label(root, text="Password").grid(row=1, column=0, padx=8, pady=6, sticky="e")
    password = tk.Entry(root, show="*")
    password.grid(row=1, column=1, padx=8, pady=6)
    username.focus_set()

    def submit() -> None:
        result["username"] = username.get().strip()
        result["password"] = password.get()
        root.destroy()

    tk.Button(root, text="Login", width=12, command=submit).grid(row=2, column=0, columnspan=2, pady=8)
    root.bind("<Return>", lambda _event: submit())
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()

    if not result.get("username"):
        return None
    return result["username"], result["password"]
