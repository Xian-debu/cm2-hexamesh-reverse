#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m unittest discover -s tests -v
python3 -m cm2hx.verify --data "${CM2_Q4T3_DIR:-/root/projects/逆向1/work/demo-data/data}"
