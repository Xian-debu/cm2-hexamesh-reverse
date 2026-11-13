#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m unittest discover -s tests -v
DATA="${CM2_Q4T3_DIR:-$PWD/data}"
if [ -f "$DATA/cast_q4t3.dat" ]; then
  python3 -m cm2hx.verify --data "$DATA"
else
  echo "SKIP verify: cast_q4t3.dat not found under $DATA; put data in data/ or set CM2_Q4T3_DIR"
fi
