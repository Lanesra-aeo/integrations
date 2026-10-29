#!/usr/bin/env bash
# Call one Lanesra tool and print its data as JSON.
#
#   export LANESRA_API_KEY=lns_live_your_key_here
#   ./call-tool.sh get_visibility_overview
#   ./call-tool.sh get_brand_rankings '{"project":"acme","limit":5}'
#   ./call-tool.sh get_sources '{"limit":10}' | jq '.domains[] | {domain, answersCiting}'
#
# Needs curl and jq. Exits non-zero on an HTTP error or a tool error.
set -euo pipefail

: "${LANESRA_API_KEY:?Set LANESRA_API_KEY to your key (lns_live_…)}"
URL="${LANESRA_MCP_URL:-https://app.lanesra.ai/mcp}"
TOOL="${1:?Usage: $0 <tool> [arguments as JSON]}"
ARGS="${2:-}"
[ -n "$ARGS" ] || ARGS='{}'

REQUEST=$(jq -nc --arg name "$TOOL" --argjson args "$ARGS" \
  '{jsonrpc: "2.0", id: 1, method: "tools/call", params: {name: $name, arguments: $args}}')

BODY_FILE=$(mktemp)
trap 'rm -f "$BODY_FILE"' EXIT

STATUS=$(curl -sS -o "$BODY_FILE" -w '%{http_code}' -X POST "$URL" \
  -H "Authorization: Bearer $LANESRA_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  --data "$REQUEST")

# The reply is plain JSON or one event-stream frame whose "data:" line holds the JSON.
if grep -q '^data:' "$BODY_FILE"; then
  REPLY=$(sed -n 's/^data: \{0,1\}//p' "$BODY_FILE")
else
  REPLY=$(cat "$BODY_FILE")
fi

if [ "$STATUS" -ge 400 ]; then
  echo "HTTP $STATUS: $(jq -r '.error.message // .' <<<"$REPLY" 2>/dev/null || cat "$BODY_FILE")" >&2
  exit 1
fi
if jq -e '.error' <<<"$REPLY" >/dev/null; then
  echo "JSON-RPC error: $(jq -r '.error.message' <<<"$REPLY")" >&2
  exit 1
fi
if jq -e '.result.isError == true' <<<"$REPLY" >/dev/null; then
  echo "Tool error: $(jq -r '.result.content[0].text' <<<"$REPLY")" >&2
  exit 2
fi

# The data is a JSON string inside the result: parse it a second time.
jq '.result.content[0].text | fromjson? // .' <<<"$REPLY"
