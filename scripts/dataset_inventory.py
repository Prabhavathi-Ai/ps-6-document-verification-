from __future__ import annotations

import argparse
import json
from pathlib import Path

from dataset_common import GROUND_TRUTH, inventory, load_rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Report measured VeriDoc benchmark inventory statistics.")
    parser.add_argument("--ground-truth", type=Path, default=GROUND_TRUTH)
    args = parser.parse_args()
    rows = load_rows(args.ground_truth)
    print(json.dumps(inventory(rows), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
