#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${PROJECT_ROOT}"

python3 scripts/clean_dcard_salary.py \
  --input data/dcard/salary.csv \
  --output data/dcard/salary_clean.csv

python3 scripts/generate_static_report.py \
  --input data/dcard/salary_clean.csv \
  --output site

python3 - <<'PY'
from pathlib import Path
import shutil

site_root = Path("site")
subpath_root = site_root / "tw-swe-thermometer"

site_root.joinpath("methodology.html").unlink(missing_ok=True)

if subpath_root.exists():
    shutil.rmtree(subpath_root)
subpath_root.mkdir(parents=True, exist_ok=True)

for item in site_root.iterdir():
    if item.name == "tw-swe-thermometer":
        continue
    target = subpath_root / item.name
    if item.is_dir():
        shutil.copytree(item, target)
    else:
        shutil.copy2(item, target)
PY
