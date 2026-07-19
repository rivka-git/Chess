from __future__ import annotations

import pathlib
import sys


class SoundEffects:
    def __init__(self, sounds_dir: pathlib.Path) -> None:
        self._enabled = sys.platform.startswith("win")
        self._sounds = {
            "move": sounds_dir / "move.wav",
            "illegal_move": sounds_dir / "illegal_move.wav",
            "capture": sounds_dir / "capture.wav",
            "promotion": sounds_dir / "promotion.wav",
            "game_over": sounds_dir / "game_over.wav",
        }

    def play_move(self) -> None:
        self._play("move")

    def play_illegal_move(self) -> None:
        self._play("illegal_move")

    def play_capture(self) -> None:
        self._play("capture")

    def play_promotion(self) -> None:
        self._play("promotion")

    def play_game_over(self) -> None:
        self._play("game_over")

    def _play(self, name: str) -> None:
        if not self._enabled:
            return
        sound_path = self._sounds[name]
        if not sound_path.exists():
            return
        import winsound

        winsound.PlaySound(
            str(sound_path),
            winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
        )
