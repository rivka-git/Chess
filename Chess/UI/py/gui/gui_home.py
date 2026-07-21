"""GUI frontend for the home flow -- the optional second path. Login and the
Play/Room choice are windows instead of shell prompts; messages are popups.
Implements the same HomeFrontend protocol as ConsoleHomeFrontend, so
network.home_flow.run_home_flow drives it unchanged."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from gui.home_screen import prompt_home_action
from gui.login_dialog import prompt_login as gui_prompt_login
from gui.room_dialog import prompt_room_action


def _popup(kind: str, title: str, text: str) -> None:
    # Own hidden root so the popup doesn't depend on / leak a default root
    # between the flow's other short-lived Tk windows.
    root = tk.Tk()
    root.withdraw()
    getattr(messagebox, kind)(title, text, parent=root)
    root.destroy()


class GuiHomeFrontend:
    def __init__(self) -> None:
        self._username: str | None = None
        self._rating: int | None = None

    def get_credentials(self) -> tuple[str, str] | None:
        return gui_prompt_login()

    def on_logged_in(self, username: str, rating: int) -> None:
        self._username = username
        self._rating = rating

    def choose_action(self) -> str:
        return prompt_home_action(self._username, self._rating)

    def on_searching(self) -> None:
        # The flow then blocks up to a minute waiting for an opponent; a modal
        # here would block the thread that must keep reading socket replies, so
        # the notice goes to the log/console instead.
        print("Searching for an opponent (up to 1 minute)...")

    def get_room_action(self) -> tuple[str, str] | None:
        return prompt_room_action()

    def on_room_created(self, room_id: str) -> None:
        _popup("showinfo", "Room created", f"Room id: {room_id}\nShare it with the other player.")

    def show_error(self, message: str) -> None:
        _popup("showerror", "Kung-Fu Chess", message)
