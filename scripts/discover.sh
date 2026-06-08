#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
curl -X POST "$API_BASE_URL/api/jobs/discover" \
  -H "Content-Type: application/json" \
  -d '{"limit": 60}'

