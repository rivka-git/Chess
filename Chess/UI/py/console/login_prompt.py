"""Text I/O for the home screen's login step -- shell prompts, no GUI.

The password is presentation-only (per the spec), so it's read with a plain
visible prompt: hiding it (getpass) adds no real security here and breaks in
some terminals where it silently swallows input.
"""

from __future__ import annotations


def prompt_login() -> tuple[str, str]:
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    return username, password
