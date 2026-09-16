from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ROOT / "datasets"
METADATA = DATASETS / "metadata"
FIELDNAMES = [
    "document_id",
    "source_id",
    "dataset_name",
    "document_type",
    "class",
    "original_document_id",
    "tamper_type",
    "is_tampered",
    "is_exact_duplicate",
    "is_near_duplicate",
    "duplicate_of",
    "tamper_bbox",
    "mask_path",
    "split",
    "license_status",
    "source_group_id",
    "file_path",
    "sha256",
    "notes",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_original(seed: int) -> Image.Image:
    image = Image.new("RGB", (320, 200), (245, 248, 252))
    draw = ImageDraw.Draw(image)
    draw.rectangle((18, 18, 302, 182), outline=(35, 78, 128), width=3)
    draw.rectangle((30, 32, 290, 62), fill=(37, 107, 254))
    draw.text((42, 42), "SYNTHETIC DOCUMENT", fill=(255, 255, 255))
    draw.text((34, 82), f"Benchmark seed: {seed}", fill=(35, 52, 76))
    draw.rectangle((34, 108, 180, 118), fill=(165, 181, 205))
    draw.rectangle((34, 130, 250, 140), fill=(194, 205, 220))
    draw.rectangle((34, 152, 220, 162), fill=(194, 205, 220))
    return image


def copy_bytes(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def generate(seed: int) -> list[dict[str, str]]:
    original_id = "SYN-G001-ORIGINAL"
    group_id = "SYN-G001"
    original = DATASETS / "benchmark/genuine" / f"{original_id}.png"
    synthetic_original = DATASETS / "synthetic/originals" / f"{original_id}.png"
    original.parent.mkdir(parents=True, exist_ok=True)
    synthetic_original.parent.mkdir(parents=True, exist_ok=True)
    create_original(seed).save(original, format="PNG", optimize=False)
    copy_bytes(original, synthetic_original)

    exact = DATASETS / "benchmark/duplicate/SYN-G001-EXACT.png"
    synthetic_exact = DATASETS / "synthetic/duplicates/SYN-G001-EXACT.png"
    copy_bytes(original, exact)
    copy_bytes(original, synthetic_exact)

    near = DATASETS / "benchmark/near_duplicate/SYN-G001-NEAR.jpg"
    synthetic_near = DATASETS / "synthetic/duplicates/SYN-G001-NEAR.jpg"
    with Image.open(original) as image:
        resized = image.resize((280, 175), Image.Resampling.LANCZOS)
        near.parent.mkdir(parents=True, exist_ok=True)
        resized.save(near, format="JPEG", quality=85, optimize=False, progressive=False)
    copy_bytes(near, synthetic_near)

    bbox = (88, 82, 230, 105)
    tampered = DATASETS / "benchmark/tampered/images/SYN-G001-TAMPERED.png"
    mask = DATASETS / "benchmark/tampered/masks/SYN-G001-TAMPERED.pgm"
    synthetic_tampered = DATASETS / "synthetic/tampered/SYN-G001-TAMPERED.png"
    with Image.open(original) as image:
        modified = image.copy()
        ImageDraw.Draw(modified).rectangle(bbox, fill=(255, 239, 218), outline=(194, 89, 46), width=2)
        modified.save(tampered, format="PNG", optimize=False)
    mask_image = Image.new("L", (320, 200), 0)
    ImageDraw.Draw(mask_image).rectangle(bbox, fill=255)
    mask_image.save(mask, format="PPM")
    copy_bytes(tampered, synthetic_tampered)

    mixed = DATASETS / "benchmark/mixed/SYN-G001-MIXED.png"
    synthetic_mixed = DATASETS / "synthetic/tampered/SYN-G001-MIXED.png"
    copy_bytes(tampered, mixed)
    copy_bytes(tampered, synthetic_mixed)

    second = DATASETS / "benchmark/genuine/SYN-G002-ORIGINAL.png"
    with create_original(seed + 1) as second_image:
        second_image.save(second, format="PNG", optimize=False)

    def row(
        document_id: str,
        document_class: str,
        file_path: Path,
        split: str,
        original_document_id: str = "",
        tamper_type: str = "None",
        is_tampered: str = "false",
        exact_duplicate: str = "false",
        near_duplicate: str = "false",
        duplicate_of: str = "",
        tamper_bbox: str = "",
        mask_path: str = "",
        group: str = group_id,
        notes: str = "",
    ) -> dict[str, str]:
        return {
            "document_id": document_id,
            "source_id": "OR001" if group == group_id else "OR002",
            "dataset_name": "VeriDoc synthetic benchmark",
            "document_type": "invoice",
            "class": document_class,
            "original_document_id": original_document_id,
            "tamper_type": tamper_type,
            "is_tampered": is_tampered,
            "is_exact_duplicate": exact_duplicate,
            "is_near_duplicate": near_duplicate,
            "duplicate_of": duplicate_of,
            "tamper_bbox": tamper_bbox,
            "mask_path": mask_path,
            "split": split,
            "license_status": "synthetic",
            "source_group_id": group,
            "file_path": file_path.relative_to(ROOT).as_posix(),
            "sha256": sha256(file_path),
            "notes": notes,
        }

    rows = [
        row(original_id, "genuine", original, "test", notes="Base synthetic original."),
        row("SYN-G001-EXACT", "duplicate", exact, "test", original_id, exact_duplicate="true", duplicate_of=original_id, notes="Byte-identical copy; duplicate relationship is not a tamper label."),
        row("SYN-G001-NEAR", "near_duplicate", near, "test", original_id, near_duplicate="true", duplicate_of=original_id, tamper_type="resize_and_recompression"),
        row("SYN-G001-TAMPERED", "tampered", tampered, "test", original_id, "controlled_region_edit", "true", tamper_bbox="88,82,142,23", mask_path="datasets/benchmark/tampered/masks/SYN-G001-TAMPERED.pgm"),
        row("SYN-G001-MIXED", "mixed", mixed, "test", original_id, "controlled_region_edit", "true", near_duplicate="true", duplicate_of=original_id, tamper_bbox="88,82,142,23", mask_path="datasets/benchmark/tampered/masks/SYN-G001-TAMPERED.pgm", notes="Tampered variant retaining a known family relationship."),
        row("SYN-G002-ORIGINAL", "genuine", second, "validation", group="SYN-G002", notes="Independent synthetic source group."),
    ]

    with (METADATA / "ground_truth.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    manifest_path = METADATA / "benchmark_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["created_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    manifest["seed"] = seed
    manifest["splits"] = {split: {"count": sum(row["split"] == split for row in rows)} for split in ("train", "validation", "test")}
    manifest["synthetic_cases"] = [
        {"document_id": "SYN-G001-ORIGINAL", "transformation": "genuine", "seed": seed},
        {"document_id": "SYN-G001-EXACT", "transformation": "byte_copy", "seed": seed},
        {"document_id": "SYN-G001-NEAR", "transformation": "resize_and_jpeg_recompression", "seed": seed},
        {"document_id": "SYN-G001-TAMPERED", "transformation": "controlled_rectangle_edit", "seed": seed, "tamper_bbox": "88,82,142,23"},
        {"document_id": "SYN-G001-MIXED", "transformation": "tampered_family_variant", "seed": seed, "tamper_bbox": "88,82,142,23"},
        {"document_id": "SYN-G002-ORIGINAL", "transformation": "genuine", "seed": seed + 1},
    ]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the deterministic synthetic benchmark fixtures.")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    rows = generate(args.seed)
    print(json.dumps({"seed": args.seed, "generated_documents": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
