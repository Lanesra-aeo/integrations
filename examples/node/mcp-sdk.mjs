// The same first call, through the official MCP TypeScript SDK instead of plain fetch.
//
//   npm install
//   export LANESRA_API_KEY=lns_live_your_key_here
//   node mcp-sdk.mjs
//
// Use this when you already build on the SDK, for example inside an agent framework.
// The key travels as a header on every request the transport sends.

import { Client } from "@modelcontextprotocol/sdk/client/index.js"
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js"

const url = new URL(process.env.LANESRA_MCP_URL || "https://app.lanesra.ai/mcp")
const transport = new StreamableHTTPClientTransport(url, {
  requestInit: { headers: { Authorization: `Bearer ${process.env.LANESRA_API_KEY}` } },
})
const client = new Client({ name: "lanesra-integrations-example", version: "1.0.0" })

await client.connect(transport)
try {
  const { tools } = await client.listTools()
  console.log(`${tools.length} tools:`, tools.map((t) => t.name).join(", "))

  const result = await client.callTool({ name: "get_visibility_overview", arguments: {} })
  const text = result.content[0].text
  if (result.isError) throw new Error(text)
  const overview = JSON.parse(text)
  console.log(`${overview.brand}: visibility ${overview.own?.visibility}% (captured ${overview.capturedAt ?? "not yet"})`)
} finally {
  await client.close()
}
