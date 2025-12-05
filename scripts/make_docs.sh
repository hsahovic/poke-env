#!/bin/bash
set -e

cd docs
source ../.venv/bin/activate
make clean
make html

echo "Documentation built successfully in docs/build/html/"

