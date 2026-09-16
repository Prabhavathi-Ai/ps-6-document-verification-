from __future__ import annotations

import csv
from pathlib import Path

from scripts.dataset_common import GROUND_TRUTH, inventory, load_rows, validate_rows
from scripts.generate_synthetic_benchmark import generate


def test_ground_truth_loads_and_ids_are_unique() -> None:
    rows = load_rows()
    ids = [row["document_id"] for row in rows]
    assert rows
    assert len(ids) == len(set(ids))


def test_classes_and_relationships_are_valid() -> None:
    rows = load_rows()
    assert {row["class"] for row in rows} == {"genuine", "duplicate", "near_duplicate", "tampered", "mixed"}
    assert validate_rows(rows) == []


def test_exact_duplicate_has_identical_hash() -> None:
    rows = {row["document_id"]: row for row in load_rows()}
    assert rows["SYN-G001-EXACT"]["sha256"] == rows["SYN-G001-ORIGINAL"]["sha256"]
    assert rows["SYN-G001-EXACT"]["is_tampered"] == "false"


def test_near_duplicate_changes_file_with_known_relationship() -> None:
    rows = {row["document_id"]: row for row in load_rows()}
    assert rows["SYN-G001-NEAR"]["duplicate_of"] == "SYN-G001-ORIGINAL"
    assert rows["SYN-G001-NEAR"]["sha256"] != rows["SYN-G001-ORIGINAL"]["sha256"]


def test_tampered_sample_has_mask_and_ground_truth_region() -> None:
    rows = {row["document_id"]: row for row in load_rows()}
    tampered = rows["SYN-G001-TAMPERED"]
    assert tampered["is_tampered"] == "true"
    assert tampered["tamper_bbox"] == "88,82,142,23"
    assert Path(tampered["mask_path"]).exists() or (Path.cwd() / tampered["mask_path"]).exists()


def test_generator_is_deterministic_for_same_seed() -> None:
    first = {row["document_id"]: row["sha256"] for row in generate(42)}
    second = {row["document_id"]: row["sha256"] for row in generate(42)}
    assert first == second


def test_validator_rejects_broken_metadata_fixture(tmp_path: Path) -> None:
    rows = load_rows()
    rows[0]["file_path"] = "datasets/benchmark/genuine/missing.png"
    broken = tmp_path / "broken.csv"
    with broken.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    errors = validate_rows(load_rows(broken))
    assert any("missing file" in error for error in errors)


def test_inventory_matches_manifest_rows() -> None:
    rows = load_rows(GROUND_TRUTH)
    report = inventory(rows)
    assert report["total_documents"] == len(rows) == 6
    assert report["by_class"] == {"genuine": 2, "duplicate": 1, "near_duplicate": 1, "tampered": 1, "mixed": 1}
    assert report["missing_files"] == []


def test_duplicate_parent_relationships_resolve() -> None:
    rows = load_rows()
    known_ids = {row["document_id"] for row in rows}
    assert all(not row["duplicate_of"] or row["duplicate_of"] in known_ids for row in rows)


def test_source_groups_do_not_leak_between_splits() -> None:
    rows = load_rows()
    groups: dict[str, set[str]] = {}
    for row in rows:
        groups.setdefault(row["source_group_id"], set()).add(row["split"])
    assert all(len(splits) == 1 for splits in groups.values())


def test_boolean_ground_truth_values_are_consistent() -> None:
    rows = load_rows()
    for row in rows:
        assert row["is_tampered"] in {"true", "false"}
        assert row["is_exact_duplicate"] in {"true", "false"}
        assert row["is_near_duplicate"] in {"true", "false"}


def test_validator_rejects_invalid_class() -> None:
    rows = load_rows()
    rows[0]["class"] = "fraud_score"
    errors = validate_rows(rows)
    assert any("invalid class" in error for error in errors)
