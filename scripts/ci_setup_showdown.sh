#!/usr/bin/env bash
set -euo pipefail

cd pokemon-showdown

npm install
cp config/config-example.js config/config.js
sed -i 's/backdoor = true/backdoor = false/g' config/config.js
sed -i 's/simulatorprocesses = 1/simulatorprocesses = 2/g' config/config.js
sed -i 's/workers = 1/workers = 2/g' config/config.js

node pokemon-showdown start --no-security --max-old-space-size=3000 &

until curl --output /dev/null --silent --head --fail http://localhost:8000; do
  sleep 0.01
done

sleep 1
