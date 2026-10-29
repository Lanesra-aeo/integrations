# Node.js examples

Node.js 20 or later. `lanesra.mjs`, `quickstart.mjs` and `weekly-report.mjs` use only the built-in `fetch`, so there is nothing to install for them.

```bash
cd examples/node
export LANESRA_API_KEY=lns_live_your_key_here
node quickstart.mjs
```

| File | What it does |
| --- | --- |
| [`lanesra.mjs`](lanesra.mjs) | The client: one JSON-RPC call per `POST`, both response forms, errors as exceptions, retries on `502`, `503` and `504` |
| [`quickstart.mjs`](quickstart.mjs) | Lists the projects your key reads and prints each one's headline numbers |
| [`weekly-report.mjs`](weekly-report.mjs) | Headline numbers, top brands and most cited sites, printed or posted to Slack |
| [`mcp-sdk.mjs`](mcp-sdk.mjs) | The first call through the official MCP TypeScript SDK. Run `npm install` first |

`weekly-report.mjs` reads `LANESRA_PROJECT`, needed only when the key reads several projects, and `SLACK_WEBHOOK_URL`, without which the report is printed.

## Using the client

```js
import { Lanesra, LanesraHTTPError, LanesraToolError } from "./lanesra.mjs"

const client = new Lanesra()

try {
  const history = await client.call("get_visibility_history", { project: "acme", from: "2026-10-01", to: "2026-10-28" })
  console.log(history.dates, history.brands)
} catch (e) {
  if (e instanceof LanesraHTTPError) console.error(`Lanesra refused the key: ${e.message} (reason: ${e.reason})`)
  else if (e instanceof LanesraToolError) console.error(e.message) // written for a person to read
  else throw e
}
```

Arguments that are `undefined` or `null` are not sent, so optional settings can be passed straight through.
