"""Event type constants published on the server EventBus."""

GAME_STARTED = "game_started"
MOVE_MADE = "move_made"
PIECE_CAPTURED = "piece_captured"
PIECE_PROMOTED = "piece_promoted"
GAME_ENDED = "game_ended"
ELO_UPDATED = "elo_updated"

# Activity events (login/matchmaking/rooms/disconnect) -- for the activity log.
LOGIN_SUCCEEDED = "login_succeeded"
MATCH_FOUND = "match_found"
ROOM_CREATED = "room_created"
ROOM_JOINED = "room_joined"
PLAYER_DISCONNECTED = "player_disconnected"
