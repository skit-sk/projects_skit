#!/bin/bash
# agent-browser wrapper — forces writable HOME and socket dir
BROWSER_TEMP="/home/user_aioc/workspace/tools/browser-temp"
export HOME=$BROWSER_TEMP
export AGENT_BROWSER_STATE_DIR=$BROWSER_TEMP
export AGENT_BROWSER_SOCKET_DIR=$BROWSER_TEMP/sockets
export XDG_RUNTIME_DIR=$BROWSER_TEMP
export LD_LIBRARY_PATH="$BROWSER_TEMP/pango_libs/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
export PATH="/home/user_aioc/.local/bin:$PATH"

mkdir -p $BROWSER_TEMP/sockets 2>/dev/null

exec /home/user_aioc/.local/lib/node_modules/agent-browser/bin/agent-browser-linux-x64 "$@"
