#!/bin/bash
# Playwright wrapper — source env and run a Python snippet
source "$(dirname "$0")/../config/env.sh"
exec python3 "$@"
