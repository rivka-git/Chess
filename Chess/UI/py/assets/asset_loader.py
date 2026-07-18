from __future__ import annotations
import json
import pathlib
from assets.img import Img

PIECE_STATES = ("idle", "move", "jump", "short_rest", "long_rest")
# __file__ is Chess/UI/py/assets/asset_loader.py; pieces2/ and board.png live under Chess/UI/
PIECES_DIR = pathlib.Path(__file__).parent.parent.parent / "pieces2"
BOARD_PATH = pathlib.Path(__file__).parent.parent.parent / "board.png"


class AssetLoader:
    def __init__(self):
        self.board_img: Img | None = None
        # { piece_key: { state_name: {"config": dict, "frames": list[Img]} } }
        self._cache: dict[str, dict[str, dict]] = {}

    @staticmethod
    def _read_img(path: pathlib.Path) -> Img | None:
        """Read image safely, handling Unicode paths via numpy. Returns None if empty/corrupt."""
        import numpy as np
        import cv2
        with open(str(path), 'rb') as f:
            data = f.read()
        if not data:
            return None
        arr = np.array(bytearray(data), dtype=np.uint8)
        img_obj = Img()
        img_obj.img = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
        if img_obj.img is None:
            return None
        return img_obj

    @staticmethod
    def _make_placeholder(cell_size: int) -> Img:
        """Create a visible magenta placeholder for missing/corrupt sprites,
        so a broken asset shows up as an obvious marker instead of silently
        vanishing from the board.
        """
        import cv2
        import numpy as np
        img_obj = Img()
        img_obj.img = np.full((cell_size, cell_size, 4), (255, 0, 255, 255), dtype=np.uint8)
        cv2.putText(
            img_obj.img, "?",
            (cell_size // 3, int(cell_size * 0.7)),
            cv2.FONT_HERSHEY_SIMPLEX, cell_size / 60,
            (0, 0, 0, 255), thickness=max(1, cell_size // 25), lineType=cv2.LINE_AA,
        )
        return img_obj

    def load_all(self, cell_size: int) -> None:
        self.board_img = self._read_img(BOARD_PATH)
        for piece_dir in sorted(PIECES_DIR.iterdir()):
            if not piece_dir.is_dir():
                continue
            key = piece_dir.name          # e.g. "BW", "KB"
            self._cache[key] = {}
            for state in PIECE_STATES:
                state_dir = piece_dir / "states" / state
                if not state_dir.exists():
                    continue
                config = json.loads((state_dir / "config.json").read_text())
                sprites_dir = state_dir / "sprites"
                frames = []
                for f in sorted(sprites_dir.iterdir(), key=lambda p: int(p.stem)):
                    img_obj = self._read_img(f)
                    if img_obj is None:
                        img_obj = self._make_placeholder(cell_size)
                    else:
                        import cv2
                        img_obj.img = cv2.resize(img_obj.img, (cell_size, cell_size), interpolation=cv2.INTER_AREA)
                    frames.append(img_obj)
                self._cache[key][state] = {"config": config, "frames": frames}

    def get_state_data(self, piece_key: str, state_name: str) -> dict:
        """Return {"config": ..., "frames": [...]} for a piece/state."""
        return self._cache[piece_key][state_name]

    @staticmethod
    def piece_key(token: str) -> str:
        """Convert board token like 'wB' → 'BW', 'bK' → 'KB'."""
        color, kind = token[0], token[1]
        color_suffix = "W" if color == "w" else "B"
        return kind + color_suffix
