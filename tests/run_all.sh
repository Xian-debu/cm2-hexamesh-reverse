#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m unittest discover -s tests -v
DATA="${CM2_Q4T3_DIR:-/root/projects/逆向1/work/demo-data/data}"
if [ -d "$DATA" ]; then
  python3 -m cm2hx.verify --data "$DATA"
else
  echo "SKIP verify: q4t3 data dir not found ($DATA); set CM2_Q4T3_DIR to run oracle checks"
fi
