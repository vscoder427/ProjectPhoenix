#!/bin/bash
set -euo pipefail

# shellcheck source=/dev/null
if [ -f ".env" ]; then
  source .env
fi

uvicorn api.app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
