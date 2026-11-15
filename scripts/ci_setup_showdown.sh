#!/usr/bin/env bash
set -euo pipefail

cd pokemon-showdown

npm install --engine-strict
sed -e 's/backdoor = true/backdoor = false/g' \
    -e 's/simulatorprocesses = 1/simulatorprocesses = 2/g' \
    -e 's/workers = 1/workers = 2/g' \
    config/config-example.js > config/config.js

node --max-old-space-size=3000 pokemon-showdown start --no-security > server.log 2>&1 &
server_pid=$!
startup_timeout=${SHOWDOWN_STARTUP_TIMEOUT:-60}
deadline=$((SECONDS + startup_timeout))

while true; do
  if ! kill -0 "$server_pid" 2>/dev/null; then
    echo "Showdown exited before becoming ready" >&2
    cat server.log >&2
    wait "$server_pid" || exit $?
    exit 1
  fi
  if ((SECONDS >= deadline)); then
    echo "Showdown did not become ready within $startup_timeout seconds" >&2
    cat server.log >&2
    kill "$server_pid" 2>/dev/null || true
    exit 1
  fi
  if curl --output /dev/null --silent --head --fail \
      --connect-timeout 1 --max-time 2 http://localhost:8000; then
    break
  fi
  sleep 1
done
