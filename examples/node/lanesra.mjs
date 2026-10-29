// A minimal client for the Lanesra MCP endpoint. Node.js 20 or later, no dependencies.
//
//   import { Lanesra } from "./lanesra.mjs"
//
//   const client = new Lanesra()                 // reads LANESRA_API_KEY
//   const overview = await client.call("get_visibility_overview")
//   console.log(overview.capturedAt, overview.own.visibility)
//
// Every call is one JSON-RPC request in a POST. The server answers with plain JSON
// or with a single Server-Sent Events frame; both are handled here. A tool's data
// is a JSON string inside result.content[0].text, which call() parses for you.

export const DEFAULT_URL = "https://app.lanesra.ai/mcp"

// Worth retrying: the server or a proxy in front of it was briefly unavailable.
const RETRY_STATUSES = new Set([502, 503, 504])

export class LanesraError extends Error {
  name = "LanesraError"
}

/**
 * The request was refused before any tool ran: 401, 403, 405 and the like.
 * `reason` is set on a 403 (no_plan, billing_lapsed, company_suspended or
 * user_suspended). Retrying with the same key never clears a 401 or 403.
 */
export class LanesraHTTPError extends LanesraError {
  name = "LanesraHTTPError"
  constructor(status, message, code = null, reason = null) {
    super(`HTTP ${status}: ${message}`)
    Object.assign(this, { status, code, reason })
  }
}

/** A JSON-RPC error returned with HTTP 200, such as an unknown method or invalid arguments. */
export class LanesraRPCError extends LanesraError {
  name = "LanesraRPCError"
  constructor(code, message) {
    super(`JSON-RPC error ${code}: ${message}`)
    this.code = code
  }
}

/** The tool ran and could not answer. The message is written for a person to read. */
export class LanesraToolError extends LanesraError {
  name = "LanesraToolError"
}

/** Every JSON-RPC message in a response body, whichever of the two forms it came in. */
export function parseBody(body, contentType = "") {
  const trimmed = body.trimStart()
  if (!contentType.includes("text/event-stream") && (trimmed.startsWith("{") || trimmed.startsWith("["))) {
    const parsed = JSON.parse(body)
    return Array.isArray(parsed) ? parsed : [parsed]
  }
  // Events are separated by a blank line; an event's data may span several "data:" lines.
  const messages = []
  for (const event of body.replace(/\r\n/g, "\n").split("\n\n")) {
    const data = event
      .split("\n")
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice(5).replace(/^ /, ""))
    if (data.length) messages.push(JSON.parse(data.join("\n")))
  }
  return messages
}

/** The data a tool returned: its text parsed as JSON, or the text itself when it is not JSON. */
export function toolData(result) {
  const text = (result.content ?? [])
    .filter((c) => c.type === "text")
    .map((c) => c.text ?? "")
    .join("\n")
  if (result.isError) throw new LanesraToolError(text || "The tool returned an error with no message.")
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

export class Lanesra {
  #nextId = 1

  constructor({ apiKey = process.env.LANESRA_API_KEY, url = process.env.LANESRA_MCP_URL || DEFAULT_URL, timeoutMs = 60_000, retries = 2, retryDelayMs = 1000 } = {}) {
    if (!apiKey) throw new LanesraError("No API key: set LANESRA_API_KEY, or pass apiKey. Create one under Integrations → API keys.")
    Object.assign(this, { apiKey, url, timeoutMs, retries, retryDelayMs })
  }

  /** Call one tool and return its parsed data. Arguments left undefined or null are not sent. */
  async call(tool, args = {}) {
    const clean = Object.fromEntries(Object.entries(args).filter(([, v]) => v !== undefined && v !== null))
    return toolData(await this.request("tools/call", { name: tool, arguments: clean }))
  }

  /** Every tool this key can use, with its description and argument schema. */
  async listTools() {
    return (await this.request("tools/list")).tools
  }

  /** Send one JSON-RPC request and return its `result`. */
  async request(method, params) {
    const id = this.#nextId++
    const payload = { jsonrpc: "2.0", id, method, ...(params === undefined ? {} : { params }) }
    const { status, contentType, body } = await this.#post(JSON.stringify(payload))

    let messages = []
    try {
      messages = body.trim() ? parseBody(body, contentType) : []
    } catch {
      // Not JSON-RPC at all, such as a proxy's HTML error page.
      if (status < 400) throw new LanesraError(`Unreadable response (HTTP ${status}): ${body.slice(0, 500)}`)
    }

    if (status >= 400) {
      const error = messages.find((m) => m.error)?.error ?? {}
      throw new LanesraHTTPError(status, error.message || body.slice(0, 500), error.code ?? null, error.data?.reason ?? null)
    }

    const reply = messages.find((m) => m.id === id)
    if (!reply) throw new LanesraError(`No response to request ${id} in the body: ${body.slice(0, 500)}`)
    if (reply.error) throw new LanesraRPCError(reply.error.code, reply.error.message)
    return reply.result
  }

  async #post(body) {
    for (let attempt = 0; ; attempt++) {
      try {
        const res = await fetch(this.url, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${this.apiKey}`,
            "Content-Type": "application/json",
            Accept: "application/json, text/event-stream",
            "User-Agent": "lanesra-integrations-node/1.0",
          },
          body,
          signal: AbortSignal.timeout(this.timeoutMs),
        })
        if (!RETRY_STATUSES.has(res.status) || attempt >= this.retries) {
          return { status: res.status, contentType: res.headers.get("content-type") ?? "", body: await res.text() }
        }
      } catch (e) {
        // A network error or a timeout.
        if (attempt >= this.retries) throw e
      }
      await new Promise((resolve) => setTimeout(resolve, this.retryDelayMs * 2 ** attempt))
    }
  }
}
