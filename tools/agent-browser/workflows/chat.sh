#!/bin/bash
# chat.sh - AI Chat REPL для управления браузером естественным языком
# Использует Vercel AI Gateway

INSTRUCTION="${1:-}"

if [ -z "$INSTRUCTION" ]; then
    echo "=== agent-browser AI Chat REPL ==="
    echo "Usage: ./chat.sh \"open google.com and search for cats\""
    echo "       ./chat.sh  (for interactive mode)"
    echo ""
    echo "Environment variables needed:"
    echo "  AI_GATEWAY_API_KEY  - Vercel AI Gateway API key"
    echo "  AI_GATEWAY_MODEL    - Model (default: anthropic/claude-sonnet-4-6)"
    echo ""
    agent-browser chat
else
    echo "=== agent-browser AI Chat ==="
    echo "Instruction: $INSTRUCTION"
    echo ""
    agent-browser chat "$INSTRUCTION"
fi