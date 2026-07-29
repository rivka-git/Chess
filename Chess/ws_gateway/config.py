"""WebSocket Gateway configuration constants."""

import os

HOST = "0.0.0.0"
PORT = 8765
TICK_MS = 50
DISCONNECT_TIMEOUT_S = 20

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://chess:chess@localhost:5432/chess")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
