from __future__ import annotations

import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
GROUND_TRUTH = ROOT / "datasets/metadata/ground_truth.csv"
REQUIRED_COLUMNS = {
    "document_id", "source_id", "dataset_name", "document_type", "class",
    "original_document_id", "tamper_type", "is_tampered", "is_exact_duplicate",
    "is_near_duplicate", "duplicate_of", "tamper_bbox", "mask_path", "split",
    "license_status", "source_group_id", "file_path", "sha256", "notes",
}
VALID_CLASSES = {"genuine", "duplicate", "near_duplicate", "tampered", "mixed"}
VALID_SPLITS = {"train", "validation", "test"}
BOOLEAN_VALUES = {"true", "false"}


def load_rows(path: Path = GROUND_TRUTH) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing ground-truth columns: {', '.join(sorted(missing))}")
        return list(reader)


def resolve_local(relative_path: str) -> Path:
    candidate = (ROOT / relative_path).resolve()
    if ROOT not in candidate.parents and candidate != ROOT:
        raise ValueError(f"Path escapes repository: {relative_path}")
    return candidate


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_rows(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    document_ids = [row["document_id"] for row in rows]
    if len(document_ids) != len(set(document_ids)):
        errors.append("document_id values must be unique")
    known_ids = set(document_ids)
    group_splits: dict[str, set[str]] = defaultdict(set)

    for index, row in enumerate(rows, start=2):
        prefix = f"row {index}"
        if row["class"] not in VALID_CLASSES:
            errors.append(f"{prefix}: invalid class {row['class']!r}")
        if row["split"] not in VALID_SPLITS:
            errors.append(f"{prefix}: invalid split {row['split']!r}")
        for field in ("is_tampered", "is_exact_duplicate", "is_near_duplicate"):
            if row[field].lower() not in BOOLEAN_VALUES:
                errors.append(f"{prefix}: {field} must be true or false")
        if row["duplicate_of"] and row["duplicate_of"] not in known_ids:
            errors.append(f"{prefix}: duplicate_of parent does not exist")
        if row["file_path"]:
            try:
                file_path = resolve_local(row["file_path"])
                if not file_path.is_file():
                    errors.append(f"{prefix}: missing file {row['file_path']}")
                elif row["sha256"] and file_sha256(file_path) != row["sha256"]:
                    errors.append(f"{prefix}: SHA-256 mismatch for {row['file_path']}")
                if file_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".ppm", ".pgm"}:
                    try:
                        with Image.open(file_path) as image:
                            image.verify()
                    except Exception as exc:
                        errors.append(f"{prefix}: unreadable image {row['file_path']}: {exc}")
            except ValueError as exc:
                errors.append(f"{prefix}: {exc}")
        if row["mask_path"]:
            try:
                if not resolve_local(row["mask_path"]).is_file():
                    errors.append(f"{prefix}: missing mask {row['mask_path']}")
            except ValueError as exc:
                errors.append(f"{prefix}: {exc}")
        group_splits[row["source_group_id"]].add(row["split"])

    for group, splits in group_splits.items():
        if len(splits) > 1:
            errors.append(f"source_group_id {group} leaks across splits: {sorted(splits)}")
    return errors


def inventory(rows: list[dict[str, str]]) -> dict[str, object]:
    missing = [row["file_path"] for row in rows if row["file_path"] and not resolve_local(row["file_path"]).is_file()]
    return {
        "total_documents": len(rows),
        "by_dataset": dict(Counter(row["dataset_name"] for row in rows)),
        "by_class": dict(Counter(row["class"] for row in rows)),
        "by_document_type": dict(Counter(row["document_type"] for row in rows)),
        "by_split": dict(Counter(row["split"] for row in rows)),
        "tampered_documents": sum(row["is_tampered"].lower() == "true" for row in rows),
        "genuine_documents": sum(row["class"] == "genuine" for row in rows),
        "exact_duplicates": sum(row["is_exact_duplicate"].lower() == "true" for row in rows),
        "near_duplicates": sum(row["is_near_duplicate"].lower() == "true" for row in rows),
        "documents_with_masks": sum(bool(row["mask_path"]) for row in rows),
        "missing_files": missing,
    }
