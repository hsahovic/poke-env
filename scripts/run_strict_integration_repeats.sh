#!/usr/bin/env bash
set -u
set -o pipefail

N=100
SLEEP_SECONDS=10

if ! command -v pytest >/dev/null 2>&1; then
  echo "Error: pytest is not installed or not available in PATH." >&2
  echo "Install test dependencies and ensure pytest is available before running this script." >&2
  exit 1
fi

for i in $(seq 1 "$N"); do
  echo "[$i/$N] Running: pytest strict_integration_tests/"
  pytest strict_integration_tests/
  exit_code=$?

  if [ "$exit_code" -ne 0 ]; then
    echo "Pytest failed on iteration $i with exit code $exit_code. Stopping." >&2
    exit "$exit_code"
  fi

  if [ "$i" -lt "$N" ]; then
    echo "Iteration $i passed. Sleeping ${SLEEP_SECONDS}s before next run..."
    sleep "$SLEEP_SECONDS"
  fi
done

echo "All $N runs of strict_integration_tests passed successfully."
