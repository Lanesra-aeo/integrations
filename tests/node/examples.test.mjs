// Offline tests for the Node examples. No key and no network: a local stub server plays Lanesra.
//
//   node --test tests/node/examples.test.mjs

import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import { createServer } from "node:http"
import { after, before, beforeEach, describe, test } from "node:test"
import { Lanesra, LanesraHTTPError, LanesraRPCError, LanesraToolError, parseBody, toolData } from "../../examples/node/lanesra.mjs"
import { buildReport } from "../../examples/node/weekly-report.mjs"

const fixture = (name) => JSON.parse(readFileSync(new URL(`../fixtures/${name}.json`, import.meta.url), "utf8"))
const toolResult = (data, isError = false) => ({
  content: [{ type: "text", text: typeof data === "string" ? data : JSON.stringify(data) }],
  ...(isError ? { isError: true } : {}),
})

const calls = []
let flakyLeft = 0

/** Answers like the Lanesra endpoint, choosing the case from the key and the tool name. */
function stub(req, res) {
  let raw = ""
  req.on("data", (chunk) => (raw += chunk))
  req.on("end", () => {
    const body = JSON.parse(raw)
    calls.push({ headers: req.headers, body })
    const tool = body.params?.name
    const id = body.id
    const send = (status, message, { sse = true, text, contentType } = {}) => {
      const payload = text ?? (sse && status === 200 ? `event: message\ndata: ${JSON.stringify(message)}\n\n` : JSON.stringify(message))
      res.writeHead(status, { "Content-Type": contentType ?? (text ? "text/html" : sse && status === 200 ? "text/event-stream" : "application/json") })
      res.end(payload)
    }

    if (req.headers.authorization === "Bearer lns_live_revoked") {
      return send(401, { jsonrpc: "2.0", error: { code: -32001, message: "Unauthorized: send a Lanesra key" }, id: null })
    }
    if (req.headers.authorization === "Bearer lns_live_lapsed") {
      const error = { code: -32002, message: "Billing for this account has lapsed", data: { reason: "billing_lapsed" } }
      return send(403, { jsonrpc: "2.0", error, id: null })
    }
    if (tool === "flaky" && flakyLeft > 0) {
      flakyLeft--
      return send(503, null, { text: "<html>Service Unavailable</html>" })
    }
    if (body.method === "tools/list") return send(200, { jsonrpc: "2.0", id, result: { tools: [{ name: "get_visibility_overview" }] } })
    if (tool === "rpc_error") return send(200, { jsonrpc: "2.0", id, error: { code: -32602, message: "Invalid arguments" } })
    if (tool === "tool_error") return send(200, { jsonrpc: "2.0", id, result: toolResult('No project "nope" on this account', true) })
    if (tool === "plain_json") return send(200, { jsonrpc: "2.0", id, result: toolResult({ form: "json" }) }, { sse: false })
    if (tool === "echo") return send(200, { jsonrpc: "2.0", id, result: toolResult(body.params.arguments) })
    // Everything else answers like the real server: one event-stream frame.
    return send(200, { jsonrpc: "2.0", id, result: toolResult({ form: "sse", tool }) })
  })
}

describe("parsing", () => {
  test("plain JSON body", () => assert.deepEqual(parseBody('{"id":1}', "application/json"), [{ id: 1 }]))
  test("event-stream body", () => assert.deepEqual(parseBody('event: message\ndata: {"id":1,"result":{}}\n\n', "text/event-stream"), [{ id: 1, result: {} }]))
  test("event-stream with CRLF and split data lines", () =>
    assert.deepEqual(parseBody('event: message\r\ndata: {"id":1,\r\ndata: "result":{}}\r\n\r\n', "text/event-stream"), [{ id: 1, result: {} }]))
  test("tool data parses JSON text", () => assert.deepEqual(toolData(toolResult({ a: 1 })), { a: 1 }))
  test("tool data returns text that is not JSON", () => assert.equal(toolData(toolResult("plain words")), "plain words"))
  test("tool data throws on isError", () => assert.throws(() => toolData(toolResult("pass one as `project`", true)), LanesraToolError))
})

describe("client", () => {
  let server
  let url
  before(async () => {
    server = createServer(stub)
    await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve))
    url = `http://127.0.0.1:${server.address().port}/mcp`
  })
  after(() => server.close())
  beforeEach(() => (calls.length = 0))
  const client = (apiKey = "lns_live_test", opts = {}) => new Lanesra({ apiKey, url, ...opts })

  test("sends the required headers", async () => {
    await client().call("get_visibility_overview")
    const h = calls[0].headers
    assert.equal(h.authorization, "Bearer lns_live_test")
    assert.equal(h.accept, "application/json, text/event-stream")
    assert.equal(h["content-type"], "application/json")
  })
  test("reads an event-stream reply", async () => assert.deepEqual(await client().call("get_sources"), { form: "sse", tool: "get_sources" }))
  test("reads a plain JSON reply", async () => assert.deepEqual(await client().call("plain_json"), { form: "json" }))
  test("drops arguments left undefined or null", async () => assert.deepEqual(await client().call("echo", { project: undefined, locale: null, limit: 5 }), { limit: 5 }))
  test("lists tools", async () => assert.deepEqual(await client().listTools(), [{ name: "get_visibility_overview" }]))
  test("401 throws with status and code", async () => {
    await assert.rejects(client("lns_live_revoked").call("get_visibility_overview"), (e) => e instanceof LanesraHTTPError && e.status === 401 && e.code === -32001)
  })
  test("403 carries the reason", async () => {
    await assert.rejects(client("lns_live_lapsed").call("get_visibility_overview"), (e) => e instanceof LanesraHTTPError && e.status === 403 && e.reason === "billing_lapsed")
  })
  test("JSON-RPC error throws", async () => await assert.rejects(client().call("rpc_error"), (e) => e instanceof LanesraRPCError && e.code === -32602))
  test("tool error throws with its message", async () => await assert.rejects(client().call("tool_error"), /No project "nope"/))
  test("retries a 503 then succeeds", async () => {
    flakyLeft = 1
    assert.equal((await client("lns_live_test", { retries: 2, retryDelayMs: 1 }).call("flaky")).tool, "flaky")
    assert.equal(calls.length, 2)
  })
  test("gives up after the last retry", async () => {
    flakyLeft = 5
    await assert.rejects(client("lns_live_test", { retries: 0 }).call("flaky"), (e) => e instanceof LanesraHTTPError && e.status === 503)
  })
  test("a missing key is reported", () => assert.throws(() => new Lanesra({ apiKey: "", url }), /LANESRA_API_KEY/))
})

describe("weekly report", () => {
  test("builds from real result shapes", () => {
    const report = buildReport(fixture("overview"), fixture("rankings"), fixture("sources"))
    assert.match(report, /\*Acme: AI visibility\*/)
    assert.match(report, /Visibility: \*78\.3%\*/)
    assert.match(report, /1\. Acme \(you\)/)
    assert.match(report, /site-1\.example: cited in 11 answers/)
  })
  test("numbers your brand by its rank when it is added below the top", () => {
    const rankings = fixture("rankings")
    const others = Array.from({ length: 5 }, (_, i) => ({ ...rankings.brands[1], isOwn: false, brand: `Brand ${i}` }))
    const own = { ...rankings.brands[0], isOwn: true }
    const report = buildReport({ ...fixture("overview"), rankAmongTracked: 9 }, { brands: [...others, own] }, fixture("sources"))
    assert.match(report, /…\n9\. Acme \(you\)/)
  })
})
