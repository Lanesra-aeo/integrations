# Connecting AI assistants

Any client that speaks MCP over streamable HTTP can use Lanesra. The easiest way is **Integrations → MCP** in the Lanesra app: pick your assistant and copy a config with your personal key already in it. This page is for building the configs by hand.

Ready-to-edit copies of each config are in [`examples/mcp-clients`](../examples/mcp-clients). Replace `lns_live_your_key_here` with your key, and keep files that carry a key out of version control.

## ChatGPT and Claude.ai

These sign in to Lanesra with OAuth, so there is no key to copy. Add a custom connector with this URL, and approve the app on the Lanesra page it sends you to:

```
https://app.lanesra.ai/mcp
```

- **ChatGPT:** Settings → Apps & Connectors → Create. Choose OAuth for authentication. If you don't see Create, turn on Developer mode under Advanced settings.
- **Claude.ai:** Settings → Connectors → Add custom connector. Leave the advanced OAuth fields empty.

## Claude Code

One command, run once in a terminal:

```bash
claude mcp add --transport http --scope user lanesra https://app.lanesra.ai/mcp --header "Authorization: Bearer lns_live_your_key_here"
```

Check it with `claude mcp list`, then start a new Claude Code session.

## Claude Desktop

Claude Desktop can't send a header to a remote server, so it goes through the `mcp-remote` bridge, which needs Node.js. Add this to `claude_desktop_config.json` (Settings → Developer → Edit Config), then quit and reopen Claude Desktop:

```json
{
  "mcpServers": {
    "lanesra": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://app.lanesra.ai/mcp", "--header", "Authorization:Bearer lns_live_your_key_here"]
    }
  }
}
```

## Cursor

`~/.cursor/mcp.json` for every project, or `.cursor/mcp.json` for one:

```json
{
  "mcpServers": {
    "lanesra": {
      "url": "https://app.lanesra.ai/mcp",
      "headers": { "Authorization": "Bearer lns_live_your_key_here" }
    }
  }
}
```

## VS Code

`.vscode/mcp.json` in your workspace. VS Code lists servers under `servers`, not `mcpServers`:

```json
{
  "servers": {
    "lanesra": {
      "type": "http",
      "url": "https://app.lanesra.ai/mcp",
      "headers": { "Authorization": "Bearer lns_live_your_key_here" }
    }
  }
}
```

## Other clients

Windsurf, Claude Code's project `.mcp.json` and most other clients read the standard block:

```json
{
  "mcpServers": {
    "lanesra": {
      "type": "http",
      "url": "https://app.lanesra.ai/mcp",
      "headers": { "Authorization": "Bearer lns_live_your_key_here" }
    }
  }
}
```

## What to ask

Once connected, ask in plain language. For example:

- "What's my AI visibility this week, and where do I rank among tracked brands?"
- "Which sources does AI read when it recommends a competitor instead of me?"
- "Has my visibility moved in the last 30 days?"
- "What does share of voice mean, and how is it calculated?"

More: [Prompts](https://docs.lanesra.ai/mcp-prompts) and [Use cases](https://docs.lanesra.ai/mcp-use-cases) on docs.lanesra.ai.

## In the browser

The Lanesra dashboard also registers read-only tools for AI agents working inside the browser, through WebMCP. This is experimental. See [WebMCP](https://docs.lanesra.ai/webmcp).
