"""UI-agnostic home-screen flow: log in (with retry), then either match via
Play or create/join a Room, until the player is seated in a game.

The concrete way to prompt the user and show messages is a HomeFrontend, so
the exact same flow drives both the shell frontend (which the CR requires) and
the GUI frontend. Returns True once seated, False if the user backed out.
"""

from __future__ import annotations

from typing import Protocol


class HomeFrontend(Protocol):
    def get_credentials(self) -> tuple[str, str] | None: ...
    def on_logged_in(self, username: str, rating: int) -> None: ...
    def choose_action(self) -> str: ...  # "play" | "room" | "quit"
    def on_searching(self) -> None: ...
    def get_room_action(self) -> tuple[str, str] | None: ...  # ("create","") | ("join", id) | None
    def on_room_created(self, room_id: str) -> None: ...
    def show_error(self, message: str) -> None: ...


class GateLike(Protocol):
    def send(self, message: dict) -> None: ...
    def wait_for(self, *message_types: str) -> dict: ...


def run_home_flow(gate: GateLike, frontend: HomeFrontend) -> bool:
    if not _login(gate, frontend):
        return False
    return _home(gate, frontend)


def _login(gate: GateLike, frontend: HomeFrontend) -> bool:
    while True:
        credentials = frontend.get_credentials()
        if credentials is None:
            return False
        username, password = credentials
        gate.send({"type": "login", "username": username, "password": password})
        reply = gate.wait_for("login_ok", "login_failed")
        if reply["type"] == "login_ok":
            frontend.on_logged_in(username, reply.get("rating"))
            return True
        frontend.show_error(reply.get("message", "Login failed."))


def _home(gate: GateLike, frontend: HomeFrontend) -> bool:
    while True:
        action = frontend.choose_action()
        if action == "quit":
            return False
        if action == "play":
            if _play(gate, frontend):
                return True
        elif action == "room":
            if _room(gate, frontend):
                return True


def _play(gate: GateLike, frontend: HomeFrontend) -> bool:
    frontend.on_searching()
    gate.send({"type": "find_match"})
    reply = gate.wait_for("searching_match", "role_assigned")
    if reply["type"] == "searching_match":
        reply = gate.wait_for("role_assigned", "no_match_found")
    if reply["type"] == "no_match_found":
        frontend.show_error("Couldn't find an opponent in time.")
        return False
    gate.wait_for("state")
    return True


def _room(gate: GateLike, frontend: HomeFrontend) -> bool:
    action = frontend.get_room_action()
    if action is None:
        return False
    kind, room_id = action
    if kind == "create":
        gate.send({"type": "create_room"})
        role_assigned = gate.wait_for("role_assigned")
        gate.wait_for("state")
        frontend.on_room_created(role_assigned["room_id"])
        return True
    if kind == "join" and room_id:
        gate.send({"type": "join_room", "room_id": room_id})
        reply = gate.wait_for("role_assigned", "spectating", "room_not_found", "bad_request")
        if reply["type"] in ("role_assigned", "spectating"):
            gate.wait_for("state")
            return True
        frontend.show_error(reply.get("message", "Could not join room."))
    return False
