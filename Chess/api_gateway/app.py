"""API Gateway — HTTP service for auth and game history.

Routes:
  POST /auth/login         — login or auto-register, returns username + rating
  GET  /history/{username} — game history for a player

Run with:
  uvicorn api_gateway.app:app --host 0.0.0.0 --port 8080
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from api_gateway.auth.auth_service import AuthService
from api_gateway.auth.exceptions import InvalidCredentialsError
from api_gateway.auth.password_hasher import PasswordHasher
from api_gateway.persistence.db import create_pool
from api_gateway.persistence.game_repository import GameRepository
from api_gateway.persistence.player_repository import PlayerRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = await create_pool()
    app.state.auth = AuthService(PlayerRepository(pool), PasswordHasher())
    app.state.games = GameRepository(pool)
    yield
    await pool.close()


app = FastAPI(title="Chess API Gateway", lifespan=lifespan)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


@app.post("/auth/login")
async def login(body: LoginRequest, request: Request) -> dict:
    try:
        player = await request.app.state.auth.login_or_register(body.username, body.password)
    except InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    return {"username": player.username, "rating": player.rating}


@app.get("/history/{username}")
async def get_history(username: str, request: Request) -> dict:
    rows = await request.app.state.games.get_games_for_player(username)
    return {
        "username": username,
        "games": [
            {
                "id": row["id"],
                "room_id": row["room_id"],
                "white": row["white_username"],
                "black": row["black_username"],
                "winner": row["winner"],
                "reason": row["reason"],
                "started_at": str(row["started_at"]),
                "ended_at": str(row["ended_at"]) if row["ended_at"] else None,
            }
            for row in rows
        ],
    }
