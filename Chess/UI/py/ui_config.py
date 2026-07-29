"""Configuration for the UI layer."""

DEFAULT_BOARD_TEXT = """Board:
bR bN bB bQ bK bB bN bR
bP bP bP bP bP bP bP bP
.  .  .  .  .  .  .  .
.  .  .  .  .  .  .  .
.  .  .  .  .  .  .  .
.  .  .  .  .  .  .  .
wP wP wP wP wP wP wP wP
wR wN wB wQ wK wB wN wR
"""

import os

# WebSocket Gateway — real-time game traffic
WS_SERVER_URI = os.environ.get("WS_SERVER_URI", "ws://localhost:8765")

# API Gateway — login and history (HTTP)
API_SERVER_URL = os.environ.get("API_SERVER_URL", "http://localhost:8080")
