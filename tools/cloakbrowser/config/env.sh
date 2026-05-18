#!/bin/bash
# CloakBrowser environment
export CLOAKBROWSER_CACHE_DIR="${CLOAKBROWSER_CACHE_DIR:-/tmp/cloakbrowser}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-/tmp/cache}"
export LD_LIBRARY_PATH="/tmp/pango_libs/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
export CLOAKBROWSER_AUTO_UPDATE=false
