from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dataset_common import GROUND_TRUTH, load_rows, validate_rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate VeriDoc benchmark metadata and local files.")
    parser.add_argument("--ground-truth", type=Path, default=GROUND_TRUTH)
    args = parser.parse_args()
    try:
        rows = load_rows(args.ground_truth)
        errors = validate_rows(rows)
    except (OSError, ValueError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, indent=2))
        return 1
    result = {"valid": not errors, "records": len(rows), "errors": errors}
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
