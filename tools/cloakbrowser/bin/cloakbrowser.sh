#!/bin/bash
# CloakBrowser wrapper — source env, run Python snippet
source "$(dirname "$0")/../config/env.sh"
exec python3 "$@"
