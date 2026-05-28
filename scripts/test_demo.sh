#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
export TOKEN_SECRET="${TOKEN_SECRET:-demo-secret-change-me-for-local-runs}"
python3 -m pytest tests
