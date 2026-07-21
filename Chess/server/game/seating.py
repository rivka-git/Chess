"""Shared seating + notification logic used by matchmaking and room joins
alike: assigns a seat in a session and sends the resulting role/state."""

from __future__ import annotations

from netcommon.messages import snapshot_to_wire

_ROLE_NAMES = {"w": "white", "b": "black"}


async def seat_and_notify(session, connection) -> str | None:
    role = session.seat_next(connection)
    if role is None:
        return None
    connection.color = role
    connection.room_id = session.session_id
    await connection.send_json({
        "type": "role_assigned", "role": _ROLE_NAMES[role], "room_id": session.session_id,
    })
    await connection.send_json({
        "type": "state", "snapshot": snapshot_to_wire(session.get_viewer_snapshot(role)),
    })
    if session.is_full() and not session.started:
        session.start()
    return role
