from __future__ import annotations

from pathlib import Path
from typing import BinaryIO


class StorageError(Exception):
    pass


class StorageService:
    def __init__(self, root: str) -> None:
        self.root = Path(root).resolve()
        self.originals = self.root / "originals"
        self.processed = self.root / "processed"
        self.derived = self.root / "derived"
        self.thumbnails = self.root / "thumbnails"
        for directory in (self.originals, self.processed, self.derived, self.thumbnails):
            directory.mkdir(parents=True, exist_ok=True)

    def save(self, file_object: BinaryIO, stored_filename: str) -> str:
        target = self._safe_path(self.originals, stored_filename)
        try:
            with target.open("xb") as destination:
                while chunk := file_object.read(1024 * 1024):
                    destination.write(chunk)
        except OSError as exc:
            if target.exists():
                target.unlink(missing_ok=True)
            raise StorageError("Unable to save file") from exc
        return target.relative_to(self.root).as_posix()

    def get(self, storage_path: str) -> Path:
        target = self._safe_path(self.root, storage_path)
        if not target.is_file():
            raise FileNotFoundError(storage_path)
        return target

    def delete(self, storage_path: str) -> None:
        target = self.get(storage_path)
        try:
            target.unlink()
        except OSError as exc:
            raise StorageError("Unable to delete file") from exc

    def exists(self, storage_path: str) -> bool:
        try:
            return self.get(storage_path).is_file()
        except (FileNotFoundError, ValueError):
            return False

    def _safe_path(self, base: Path, relative_path: str) -> Path:
        candidate = (base / relative_path).resolve()
        base_path = base.resolve()
        if candidate != base_path and base_path not in candidate.parents:
            raise StorageError("Invalid storage path")
        return candidate
