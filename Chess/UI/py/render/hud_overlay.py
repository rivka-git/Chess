"""The client-side, non-board information the renderer overlays on the game
window: the room id and the disconnect countdown. Kept separate from
GameSnapshot because these are client/session concerns, not board state."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HudOverlay:
    room_id: str | None = None
    countdown_seconds: int | None = None


def overlay_from_controller(controller) -> HudOverlay:
    """Reads the overlay off a RemoteController (or returns an empty overlay
    if there isn't one, e.g. during the local single-player build)."""
    if controller is None:
        return HudOverlay()
    return HudOverlay(
        room_id=getattr(controller, "room_id", None),
        countdown_seconds=getattr(controller, "opponent_left_seconds", None),
    )
