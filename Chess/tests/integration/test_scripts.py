"""Integration tests - run .kfc scripts through the full app pipeline."""

import io
import sys
from pathlib import Path

import pytest
import app

SCRIPTS_DIR = Path(__file__).parent / "scripts"

EXPECTED = {
    "01_board_parsing.kfc": "wR wP .\n. . .",
    "02_click_to_move.kfc": ". . wR",
    "03_capture.kfc":       ". . wR",
    "04_jump.kfc":          "wR . .",
    "05_game_over.kfc":     ". wR",
}


@pytest.mark.parametrize("script_name", EXPECTED.keys())
def test_script(script_name, monkeypatch, capsys):
    script = (SCRIPTS_DIR / script_name).read_text()
    monkeypatch.setattr(sys, "stdin", io.StringIO(script))
    app.main()
    captured = capsys.readouterr()
    assert captured.out.strip() == EXPECTED[script_name]
