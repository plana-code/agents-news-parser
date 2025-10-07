#!/usr/bin/env bash
set -euo pipefail

pip3 install -r requirements.txt
python3 -m playwright install
echo "Setup complete."
