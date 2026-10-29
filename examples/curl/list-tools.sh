#!/usr/bin/env bash
# List the tools your key can use, one per line with the first sentence of its description.
#
#   export LANESRA_API_KEY=lns_live_your_key_here
#   ./list-tools.sh
#
# Needs curl and jq.
set -euo pipefail

: "${LANESRA_API_KEY:?Set LANESRA_API_KEY to your key (lns_live_…)}"
URL="${LANESRA_MCP_URL:-https://app.lanesra.ai/mcp}"

curl -sS --fail-with-body -X POST "$URL" \
  -H "Authorization: Bearer $LANESRA_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \
| sed -n -e 's/^data: \{0,1\}//p' -e t -e '/^{/p' \
| jq -r '.result.tools[] | "\(.name)\t\(.description | split(". ")[0])"'
