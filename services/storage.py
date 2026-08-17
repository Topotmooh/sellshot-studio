"""Безопасное временное хранилище."""
from __future__ import annotations

import time
import uuid
from pathlib import Path

from config import logger, settings


def _sanitize_suffix(suffix: str) -> str:
    if suffix and suffix.startswith(".") and "/" not in suffix and len(suffix) <= 8:
        return suffix
    return ".jpg"


def _base(dir_path: str) -> Path:
    p = Path(dir_path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def new_temp_path(suffix: str = ".jpg") -> Path:
    return _base(settings.TEMP_DIR) / f"{uuid.uuid4().hex}{_sanitize_suffix(suffix)}"


def new_result_path(suffix: str = ".jpg") -> Path:
    return _base(settings.RESULTS_DIR) / f"{uuid.uuid4().hex}{_sanitize_suffix(suffix)}"


def _inside(p: Path, root: Path) -> bool:
    try:
        p.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def safe_unlink(path: Path | str | None) -> None:
    """Удаляет файл ТОЛЬКО внутри рабочих директорий."""
    if path is None:
        return
    p = Path(path)
    roots = (Path(settings.TEMP_DIR), Path(settings.RESULTS_DIR))

    if not any(_inside(p, r) for r in roots):
        logger.warning("🛡 Отказ: удаление вне рабочих директорий: %s", p)
        return

    try:
        if p.exists():
            p.unlink()
    except OSError:
        logger.exception("Не удалось удалить файл: %s", p)


def cleanup_old_temp(max_age_hours: int = 24) -> int:
    """Фото пользователей не живут дольше суток."""
    removed = 0
    now = time.time()
    for root in (Path(settings.TEMP_DIR), Path(settings.RESULTS_DIR)):
        if not root.exists():
            continue
        for f in root.iterdir():
            try:
                if f.is_file() and now - f.stat().st_mtime > max_age_hours * 3600:
                    f.unlink()
                    removed += 1
            except OSError:
                pass
    return removed