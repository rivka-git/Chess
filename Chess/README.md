# Chess

A two-player real-time chess game with animated pieces, a WebSocket server, matchmaking, and persistent game history.

## Features

- Animated piece movement with sprite-based visuals
- Real-time multiplayer over WebSocket
- Room-based matchmaking (create / join a room)
- Server-side move validation via `GameEngine`
- Disconnect handling with a 20-second auto-resign countdown
- ELO rating system and game history stored in SQLite
- Event bus for decoupled server-side logic
- 91% test coverage

## Project Structure

```
Chess/
├── core/          # Game logic: board, pieces, rules, real-time arbiter
├── server/        # WebSocket server, rooms, matchmaking, ratings, persistence
├── UI/py/         # Pygame client (local + networked)
├── netcommon/     # Shared message types and defaults
├── tests/         # Unit and integration tests
├── config.py      # Client-side config (cell size, transit duration)
└── chess.db       # SQLite database (auto-created on first run)
```

## Requirements

- Python 3.10+
- Install server dependencies from the project root:
  ```
  pip install -r requirements.txt
  ```
- Install client dependencies:
  ```
  pip install -r UI/py/requirements.txt
  ```

## Running the Game

### Option 1 — One-click multiplayer (console login)

```
run_multiplayer.bat
```

Opens 3 windows: the server + two client windows with console login.

### Option 2 — One-click multiplayer (GUI login)

```
run_multiplayer_gui.bat
```

Same as above but with a tkinter login dialog instead of the console.

### Option 3 — Manual startup

**Start the server** (from the project root):
```
python -m server.server_main
```

**Start each client** (in a separate terminal):
```
python UI/py/network_main.py          # console login
python UI/py/network_main.py --gui    # GUI login
```

To connect to a remote server, pass the URI as an argument:
```
python UI/py/network_main.py ws://<host>:8765
```

## Server Configuration

Edit `server/server_config.py`:

| Setting               | Default     | Description                          |
|-----------------------|-------------|--------------------------------------|
| `HOST`                | `localhost` | Server bind address                  |
| `PORT`                | `8765`      | WebSocket port                       |
| `TICK_MS`             | `50`        | Game loop tick interval (ms)         |
| `DB_PATH`             | `chess.db`  | SQLite database file path            |
| `DISCONNECT_TIMEOUT_S`| `20`        | Seconds before a disconnected player auto-resigns |

## Running Tests

From the project root:
```
pytest
```

To generate a coverage report:
```
pytest --cov --cov-report=html
```
Then open `htmlcov/index.html` in a browser.

## How to Play

1. Start the server and two clients (see above).
2. Each client logs in (or registers automatically with a new username).
3. One player creates a room, the other joins it using the room ID.
4. White moves first — click a piece to select it, then click the destination square.
5. The game ends when a king is captured or a player disconnects for 20 seconds.
