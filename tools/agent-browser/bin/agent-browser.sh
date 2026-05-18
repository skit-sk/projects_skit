#!/bin/bash
# agent-browser wrapper — forces writable HOME and socket dir
export HOME=/tmp
export AGENT_BROWSER_STATE_DIR=/tmp/.agent-browser
export AGENT_BROWSER_SOCKET_DIR=/tmp/.agent-browser/sockets
export XDG_RUNTIME_DIR=/tmp/.agent-browser
export LD_LIBRARY_PATH="/tmp/pango_libs/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
export PATH="/home/user_aioc/.local/bin:$PATH"

mkdir -p /tmp/.agent-browser/sockets 2>/dev/null

exec /home/user_aioc/.local/lib/node_modules/agent-browser/bin/agent-browser-linux-x64 "$@"
