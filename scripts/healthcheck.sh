#!/usr/bin/env bash
set -e

PASS=0
FAIL=0

check() {
  local label="$1" cmd="$2"
  if eval "$cmd" > /dev/null 2>&1; then
    echo "  [OK]  $label"
    ((PASS++))
  else
    echo "  [FAIL] $label"
    ((FAIL++))
  fi
}

echo "=== DebtSpiral Health Check ==="
echo ""

check "Backend responds" "curl -sf http://localhost:8000/health"
check "Frontend responds" "curl -sf http://localhost:5173"
check "Personas loaded" "curl -sf http://localhost:8000/personas | python -c 'import sys,json; d=json.load(sys.stdin); assert len(d)>=4'"
check "Reset works" "curl -sf -X POST http://localhost:8000/reset"

echo ""
echo "Result: $PASS passed, $FAIL failed"

if [ "$FAIL" -gt 0 ]; then
  echo "STATUS: NOT READY"
  exit 1
else
  echo "STATUS: ALL GREEN"
  exit 0
fi
