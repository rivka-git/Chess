"""Entrypoint: python -m server.server_main"""

# 🇮🇱 הסבר: זהו נקודת הכניסה הראשית של השרת.
# כדי להפעיל את השרת, רצים: python -m server.server_main
# הקוד הזה:
# 1. מוסיף את תיקיות הפרויקט ל-sys.path כדי שה-imports יעבדו
# 2. מגדיר לוגים (הדפסות מידע לקונסול)
# 3. מפעיל את השרת באמצעות asyncio (מנגנון אסינכרוני של פייתון)

from __future__ import annotations

import asyncio
import logging
import pathlib
import sys

# מוצא את תיקיית השורש של הפרויקט (Chess/) ומוסיף אותה ואת UI/py ל-sys.path
# כך ניתן לעשות import מכל מקום בפרויקט
_CHESS_ROOT = pathlib.Path(__file__).resolve().parent.parent
_UI_PY = _CHESS_ROOT / "UI" / "py"
for _path in (_CHESS_ROOT, _UI_PY):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from server.net.ws_server import run_server  # noqa: E402


def main() -> None:
    # מגדיר את רמת הלוגים ל-INFO — יציג הודעות מידע, אזהרות, ושגיאות בקונסול
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    # מריץ את פונקציית השרת האסינכרונית run_server() עד שהשרת נסגר
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
