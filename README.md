# Lanesra integrations

Read your [Lanesra](https://lanesra.ai) AI-visibility data from your own code, reports and AI agents.

Lanesra tracks how AI answer engines (ChatGPT, Perplexity, Gemini, Copilot, Google AI Mode and AI Overviews) talk about your brand. Everything the dashboard shows is also available over one endpoint, the Lanesra MCP server, which speaks plain JSON-RPC over HTTP. This repository explains that endpoint for developers and gives you working examples to start from.

The full product documentation lives at **[docs.lanesra.ai](https://docs.lanesra.ai)**.

## What you can build

- **Scheduled reports.** Post your headline numbers to Slack or email every Monday.
- **BI dashboards.** Load visibility history and brand rankings into a warehouse, Looker Studio or Power BI.
- **Alerts.** Check visibility daily and flag a drop.
- **Custom agents.** Give your own AI agent the same tools Claude, ChatGPT and Cursor get.

## Quickstart

1. In the Lanesra app, open **Integrations → API keys** and create a key. The company owner and project Admins can create keys. It starts with `lns_live_` and is shown once. See [Authentication](docs/authentication.md).
2. Make your first call:

```bash
export LANESRA_API_KEY=lns_live_your_key_here

curl -sS -X POST https://app.lanesra.ai/mcp \
  -H "Authorization: Bearer $LANESRA_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_visibility_overview","arguments":{}}}'
```

3. Read the result. The data is a JSON string inside `result.content[0].text`. See [Making requests](docs/making-requests.md).

## Documentation

| Page | What it covers |
| --- | --- |
| [Authentication](docs/authentication.md) | Kinds of key, roles, and signing in from ChatGPT and Claude.ai |
| [Making requests](docs/making-requests.md) | The request, both response forms, and how to read a result |
| [Tools](docs/tools.md) | Every tool, its arguments and what it returns |
| [Errors](docs/errors.md) | HTTP errors, tool errors, and what to retry |
| [AI assistants](docs/ai-assistants.md) | Connecting Claude Code, Claude Desktop, Cursor, VS Code and others |

## Examples

| Folder | What is in it |
| --- | --- |
| [examples/curl](examples/curl) | Shell scripts with `curl` and `jq` |
| [examples/python](examples/python) | A small client for Python 3.10 or later with no dependencies, a weekly report, a visibility alert and a CSV export |
| [examples/node](examples/node) | The same client and report for Node.js 20 or later, with no dependencies |
| [examples/mcp-clients](examples/mcp-clients) | Ready-made configs for AI assistants |
| [examples/github-actions](examples/github-actions) | A scheduled workflow that posts the weekly report to Slack |

Each Python and Node folder also has one example using the official MCP SDK, for when you already build on it.

## Good to know

- **Answers are captured on a schedule, not live.** Every project result carries `capturedAt`. Store it with the numbers, so a report always says how current it is.
- **A key reads only its own company.** It reads every project, or the projects it was created for, within its role.
- **A key is read-only by default.** Its role decides whether it can also make changes. See [Change tools](docs/tools.md#change-tools).
- **Keep keys out of code.** Use an environment variable or a secret manager. This repository's `.gitignore` already excludes `.env`.

## Support

Questions about your account or data: [docs.lanesra.ai/support](https://docs.lanesra.ai/support). Problems with these examples: open an issue. Security reports: see [SECURITY.md](SECURITY.md).

## License

The code and documentation in this repository are released under the [MIT License](LICENSE).
