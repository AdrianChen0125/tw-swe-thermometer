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
