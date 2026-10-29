# Making requests

Lanesra's endpoint is an MCP server over streamable HTTP. You don't need an MCP library to use it: every call is one JSON-RPC request in a `POST`.

## The request

| Part | Value |
| --- | --- |
| Method | `POST` |
| URL | `https://app.lanesra.ai/mcp` |
| `Authorization` | `Bearer lns_live_…` |
| `Content-Type` | `application/json` |
| `Accept` | `application/json, text/event-stream` (both are required) |

The server is stateless. You don't need to send `initialize` first, and there is no session id to keep. `GET` and `DELETE` on `/mcp` return `405`.

## Calling a tool

Put the tool's name in `params.name` and its arguments in `params.arguments`:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "get_visibility_history",
    "arguments": { "project": "acme", "from": "2026-09-01", "to": "2026-09-28" }
  }
}
```

`tools/list` returns every tool your key can use, with a description and a JSON Schema for its arguments:

```json
{ "jsonrpc": "2.0", "id": 1, "method": "tools/list" }
```

The list depends on the key. A Viewer key gets no change tools, and a tool for a feature that is off on all your projects is left out.

## Reading the response

The body comes in one of two forms. Your code should accept both.

**Plain JSON.** The body is the JSON-RPC response.

**An event stream.** The body is one Server-Sent Events frame. The JSON-RPC response is on the `data:` line:

```
event: message
data: {"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"{…}"}]}}
```

Either way, the data you want is text inside the result. `result.content[0].text` is a JSON string, so parse it a second time:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      { "type": "text", "text": "{\"project\":\"acme\",\"brand\":\"Acme\",\"capturedAt\":\"2026-10-27T03:41:09.000Z\",…}" }
    ]
  }
}
```

If the tool couldn't answer, `result.isError` is `true` and the text says why in plain words. See [Errors](errors.md).

[`examples/python/lanesra.py`](../examples/python/lanesra.py) and [`examples/node/lanesra.mjs`](../examples/node/lanesra.mjs) do all of this in one short file each, with no dependencies.

## The result header

Every tool that reads a project's figures starts its result with the same fields, so a number is never quoted without its context:

| Field | What it is |
| --- | --- |
| `project` | The project's slug |
| `brand` | Your brand's name |
| `capturedAt` | When the data was captured |
| `period` | What the numbers cover: its kind, and its first and last day |
| `answers` | How many AI answers the numbers are computed over |
| `engines` | The answer engines included |
| `note` | Only when the period holds no answers. The figures then mean not measured yet |

**Keep `capturedAt`.** Answers are re-captured on a schedule, not live. Store the capture date with the numbers, so a report always says how current it is.

**Check `answers` before quoting a number.** When the period holds no answers, the result carries a `note` saying so. Its figures then mean "not measured yet", even where they read `0`. A metric that can't be computed, such as average position, is `null`, and so is a day with no capture in a history.

## Market, language and period

Tools that report figures read one market and language over one period, as the dashboard does:

| Argument | What it is | Default |
| --- | --- | --- |
| `locale` | A market and language, written as language and country: `en-PL` is English in Poland. `list_projects` lists each project's | The project's primary one |
| `period` | `latest` (the latest finished capture) or `all_time` | `latest` |
| `from`, `to` | A range of UTC days, `yyyy-mm-dd`, in place of `period` | |

A range must run forwards and covers at most 366 days.

## Using an MCP SDK

Any MCP client library that supports streamable HTTP works too, such as the official [TypeScript](https://github.com/modelcontextprotocol/typescript-sdk) and [Python](https://github.com/modelcontextprotocol/python-sdk) SDKs. Pass the key as an `Authorization` header on the transport. See [`examples/node/mcp-sdk.mjs`](../examples/node/mcp-sdk.mjs) and [`examples/python/mcp_sdk.py`](../examples/python/mcp_sdk.py).
