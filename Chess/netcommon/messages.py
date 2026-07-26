"""JSON (de)serialization for the client<->server wire protocol.

`snapshot_to_wire` is duck-typed (accepts anything shaped like a
`GameSnapshot`) so the server can call it without importing the UI layer's
dataclasses. `wire_to_snapshot` is used only by clients, which already have
`UI/py` on `sys.path`, so it imports `adapter.controller` lazily.

Incoming message schemas (Pydantic) are used by the server's Dispatcher to
validate and parse every client message before any handler sees it.
"""

from __future__ import annotations

from typing import Any, Annotated, Literal, Union

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Incoming client message schemas
# ---------------------------------------------------------------------------

class LoginMsg(BaseModel):
    type: Literal["login"]
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class FindMatchMsg(BaseModel):
    type: Literal["find_match"]


class CreateRoomMsg(BaseModel):
    type: Literal["create_room"]


class JoinRoomMsg(BaseModel):
    type: Literal["join_room"]
    room_id: str = Field(min_length=1)


class GetHistoryMsg(BaseModel):
    type: Literal["get_history"]


class MoveClickMsg(BaseModel):
    type: Literal["move_click"]
    row: int
    col: int


class JumpClickMsg(BaseModel):
    type: Literal["jump_click"]
    row: int
    col: int


ClientMessage = Annotated[
    Union[LoginMsg, FindMatchMsg, CreateRoomMsg, JoinRoomMsg, GetHistoryMsg, MoveClickMsg, JumpClickMsg],
    Field(discriminator="type"),
]


def parse_client_message(data: dict) -> ClientMessage:
    """Parse and validate a raw dict into a typed client message.

    Raises ``pydantic.ValidationError`` on invalid input.
    """
    from pydantic import TypeAdapter
    return TypeAdapter(ClientMessage).validate_python(data)


def snapshot_to_wire(snapshot: Any) -> dict[str, Any]:
    return {
        "clock": snapshot.clock,
        "board": [
            [
                None if piece is None else {
                    "token": piece.token,
                    "row": piece.row,
                    "col": piece.col,
                    "cooldown_until": piece.cooldown_until,
                }
                for piece in row
            ]
            for row in snapshot.board
        ],
        "pending_moves": [
            {
                "start": list(m.start),
                "end": list(m.end),
                "start_clock": m.start_clock,
                "arrival_clock": m.arrival_clock,
            }
            for m in snapshot.pending_moves
        ],
        "jumps": [
            {
                "position": list(j.position),
                "start_clock": j.start_clock,
                "land_clock": j.land_clock,
            }
            for j in snapshot.jumps
        ],
        "selected_position": list(snapshot.selected_position) if snapshot.selected_position else None,
        "legal_targets": [list(t) for t in snapshot.legal_targets],
        "game_over": snapshot.game_over,
    }


def wire_to_snapshot(data: dict[str, Any]):
    from core.engine.controller import GameSnapshot, JumpSnapshot, PendingMoveSnapshot, PieceSnapshot

    board = [
        [None if cell is None else PieceSnapshot(**cell) for cell in row]
        for row in data["board"]
    ]
    pending_moves = [
        PendingMoveSnapshot(
            start=tuple(m["start"]),
            end=tuple(m["end"]),
            start_clock=m["start_clock"],
            arrival_clock=m["arrival_clock"],
        )
        for m in data.get("pending_moves", [])
    ]
    jumps = [
        JumpSnapshot(
            position=tuple(j["position"]),
            start_clock=j["start_clock"],
            land_clock=j["land_clock"],
        )
        for j in data.get("jumps", [])
    ]
    selected = data.get("selected_position")
    return GameSnapshot(
        clock=data["clock"],
        board=board,
        pending_moves=pending_moves,
        jumps=jumps,
        selected_position=tuple(selected) if selected else None,
        legal_targets=[tuple(t) for t in data.get("legal_targets", [])],
        game_over=data.get("game_over", False),
    )
