#!/bin/sh
# The standard test run for model-bill-already-paid: the same on VM 113 and the Mac Mini.
# Sets up the pinned environment (uv.lock), then runs the whole suite. Every test must pass: there are no "known failures".
#
set -eu
cd "$(dirname "$0")/.."
uv sync --frozen --quiet
exec uv run --frozen pytest -q "$@"
