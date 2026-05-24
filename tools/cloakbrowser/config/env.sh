#!/bin/bash
# CloakBrowser environment
BROWSER_TEMP="/home/user_aioc/workspace/tools/browser-temp"
export CLOAKBROWSER_CACHE_DIR="${CLOAKBROWSER_CACHE_DIR:-$BROWSER_TEMP/cache/cloakbrowser}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$BROWSER_TEMP/cache}"
export LD_LIBRARY_PATH="$BROWSER_TEMP/pango_libs/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
export CLOAKBROWSER_AUTO_UPDATE=false
