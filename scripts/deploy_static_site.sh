#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${S3_BUCKET:-}" ]]; then
  echo "S3_BUCKET is required. Example: S3_BUCKET=my-bucket scripts/deploy_static_site.sh" >&2
  exit 1
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
S3_PREFIX="${S3_PREFIX:-}"
S3_TARGET="s3://${S3_BUCKET}"

if [[ -n "${S3_PREFIX}" ]]; then
  S3_TARGET="${S3_TARGET}/${S3_PREFIX}"
fi

cd "${PROJECT_ROOT}"

bash scripts/build_static_site.sh

aws s3 sync site/ "${S3_TARGET}" --delete

echo "Deployed static site to ${S3_TARGET}"
