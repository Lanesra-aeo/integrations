#!/usr/bin/env bash
# Add Lanesra to Claude Code for every folder you use it in. Run once.
# Replace the key, then check with: claude mcp list
claude mcp add --transport http --scope user lanesra https://app.lanesra.ai/mcp \
  --header "Authorization: Bearer lns_live_your_key_here"
