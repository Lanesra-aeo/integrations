# Authentication

Every request to `https://app.lanesra.ai/mcp` carries a credential as a bearer token:

```
Authorization: Bearer lns_live_…
```

There is no session to open and no cookie. Each request stands alone.

## Kinds of key

Every key starts with `lns_live_`. Lanesra stores only a hash of it, so a key is shown once, when it is created.

| Key | Where to find it | What it reads | Use it for |
| --- | --- | --- | --- |
| Your personal MCP key | **Integrations → MCP** | The projects you use MCP on | Your own AI assistant |
| The company key | **Integrations → API keys**, owner only | Every project in the company | Scripts that cover the whole company |
| A key you create | **Integrations → API keys → New key** | Every project, or the projects you choose | One script or one job |

Give a script a key of its own, never a person's personal key. A personal key stops working when its holder changes their password or leaves the company, and the script would break with it.

The company owner and project Admins can create keys. Creating a key needs a verified email address, and every key needs the account to have an active plan.

Full details: [API keys](https://docs.lanesra.ai/api-keys) and [Create and manage API keys](https://docs.lanesra.ai/api-keys-manage).

## A key's role

Every key has a role. The default, **Viewer**, reads every part of a project and changes nothing.

- **A custom role that reads less** narrows the key to what that role reads. A tool the role can't use answers with a tool error, not with data.
- **A role that makes changes**, such as Member, also unlocks the [change tools](tools.md#change-tools) it allows, such as adding prompts or starting a capture.
- **A key never reads or changes more** than the person who set its role can, on its projects.

The role is set in the key's row on **Integrations → API keys**. See [Roles](https://docs.lanesra.ai/roles).

## Projects

A Lanesra project is one tracked brand. A key that reads one project needs no `project` argument. A key that reads several needs `project` on every call that reads a project. The tool `list_projects` returns the slugs.

```json
{ "jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": { "name": "list_projects", "arguments": {} } }
```

## Signing in instead of a key

ChatGPT and Claude.ai connect by signing in to Lanesra with OAuth, so they need no key. The person approves the app on a Lanesra page and picks the workspace. The app then reads what that person's own key would, starting as Viewer.

A client that supports MCP authorization discovers this on its own. An unauthenticated request returns `401` with this header:

```
WWW-Authenticate: Bearer realm="lanesra", resource_metadata="https://app.lanesra.ai/.well-known/oauth-protected-resource/mcp"
```

The protected-resource metadata names the authorization server. Scripts should use a key rather than OAuth.

## Server card

The endpoint publishes an MCP server card, with no credential needed:

```bash
curl -sS https://app.lanesra.ai/mcp/server-card
```

It names the server, its transport (`streamable-http`) and the protocol versions it supports.

## Keeping keys safe

- **Store keys in an environment variable or a secret manager,** never in code, a spreadsheet or a shared document.
- **Use one key per job,** so revoking one never breaks another.
- **Revoke keys nothing uses.** The key list shows when each key was last used.
- **Replace a leaked key.** Create a new key, move your job to it, then revoke the old one.
