# Dataset and benchmark workspace

This directory contains lightweight metadata, reproducible synthetic benchmark fixtures, and empty placeholders for permitted public datasets. Large or access-restricted datasets must remain outside Git.

Run from the repository root:

```powershell
python scripts/generate_synthetic_benchmark.py --seed 42
python scripts/validate_dataset.py
python scripts/dataset_inventory.py
```

Synthetic fixtures are controlled benchmark inputs, not evidence that future detection methods generalize to real-world fraud.
