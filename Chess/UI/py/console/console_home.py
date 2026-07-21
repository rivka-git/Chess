"""Shell (text I/O) frontend for the home flow -- the CR-required option.

Login and the Play/Room choice are console prompts; the Room sub-flow reuses
the one GUI dialog the presentation depicts (gui/room_dialog.py)."""

from __future__ import annotations

from console.login_prompt import prompt_login
from gui.room_dialog import prompt_room_action


class ConsoleHomeFrontend:
    def get_credentials(self) -> tuple[str, str]:
        return prompt_login()

    def on_logged_in(self, username: str, rating: int) -> None:
        print(f"Logged in as {username} (rating {rating}).")

    def choose_action(self) -> str:
        while True:
            choice = input("1) Play  2) Room  (q to quit)\n> ").strip().lower()
            if choice == "1":
                return "play"
            if choice == "2":
                return "room"
            if choice == "q":
                return "quit"
            print("Please choose 1, 2, or q.")

    def on_searching(self) -> None:
        print("Searching for an opponent (up to 1 minute)...")

    def get_room_action(self) -> tuple[str, str] | None:
        return prompt_room_action()

    def on_room_created(self, room_id: str) -> None:
        print(f"Room created: {room_id} -- share this id with the other player.")

    def show_error(self, message: str) -> None:
        print(message)
