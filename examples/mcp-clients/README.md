# AI assistant configs

Copies of the configs the Lanesra app builds under **Integrations → MCP**. Replace `lns_live_your_key_here` with your own key. Once a file holds a real key, keep it out of version control.

| File | Client | Where it goes |
| --- | --- | --- |
| [`claude-code.sh`](claude-code.sh) | Claude Code | Run it once in a terminal |
| [`claude_desktop_config.json`](claude_desktop_config.json) | Claude Desktop | Settings → Developer → Edit Config. Needs Node.js for the `mcp-remote` bridge |
| [`cursor.mcp.json`](cursor.mcp.json) | Cursor | `~/.cursor/mcp.json`, or `.cursor/mcp.json` in one project |
| [`vscode.mcp.json`](vscode.mcp.json) | VS Code | `.vscode/mcp.json` in your workspace |
| [`standard.mcp.json`](standard.mcp.json) | Windsurf, Claude Code's `.mcp.json`, most others | Where your client reads `mcpServers` |

ChatGPT and Claude.ai need no file: they sign in to Lanesra. See [Connecting AI assistants](../../docs/ai-assistants.md).
