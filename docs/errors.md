# Errors

An error reaches you in one of two ways:

- **Before any tool runs,** as an HTTP error status with a JSON-RPC `error` in the body.
- **Once a tool has run,** as HTTP `200` with `result.isError: true` and a plain-words explanation in `result.content[0].text`.

## HTTP errors

| Status | JSON-RPC code | Meaning | What to do |
| --- | --- | --- | --- |
| `401` | `-32001` | No key, a malformed `Authorization` header, or a key that was revoked or replaced | Send exactly `Authorization: Bearer lns_live_…` with a current key |
| `403` | `-32002` | The key is valid, but the account can't use the endpoint | Read `error.data.reason`, below |
| `405` | `-32000` | A `GET` or `DELETE` request | Use `POST` |
| `400` | `-32600` | A batch carrying too many `tools/call` messages, or more than one change. `error.data.reason` is `too_many_calls` or `too_many_changes` | Send one call per request |

A `401` or `403` never clears by retrying with the same key. Stop and alert a person instead.

A key that worked before and now gets `401` was replaced or revoked. That happens when someone revoked it, when the company key was replaced, or, for a personal key, when its holder changed their password or left the company.

### 403 reasons

| `error.data.reason` | Meaning | What to do |
| --- | --- | --- |
| `no_plan` | The account has no active plan | Start a plan in the app |
| `billing_lapsed` | Billing has lapsed, so access is paused | Renew the plan. Access comes back straight away |
| `company_suspended` | The account is suspended | Contact support |
| `user_suspended` | The person a personal key belongs to is suspended | Contact support |

## Tool errors

These come back with HTTP `200`. Log or show the text: it is written for a person to read.

| Message starts with | What to do |
| --- | --- |
| This account tracks several brands - pass one as `project` | Pass `project`. The message lists the slugs |
| No project "…" on this account | The key doesn't read that project, or it doesn't exist. Call `list_projects` |
| This connection cannot use … on project "…" | The key's role doesn't read that part of the project |
| This key reads no projects | The key's holder no longer has Member or Admin access to any project |
| This key has no projects left | Every project the key was created for was deleted. Ask for a new key |
| Project "…" has no data yet | Wait for the project's first capture to finish |
| Project "…" is suspended | Contact support |
| "…" to "…" is not a date range that runs forwards | Put the earlier date in `from` |
| A range covers at most 366 days | Split the period into shorter ranges |
| Something went wrong reading this data … quote reference … | Retry later. If it keeps happening, send the reference to support |

## Empty numbers are not an error

A result with a `note` saying there are no answers in the period is a success, with `answers` at `0`. Read its figures as not measured yet, even where they show `0`. Call `get_capture_status` to see whether a capture is still running, or ask for a longer period.

## What to retry

| Situation | Retry? |
| --- | --- |
| Network error, timeout, `502`, `503` or `504` | Yes, with a growing delay, two or three times |
| `400`, `401`, `403` or `405` | No. Fix the key, the plan or the request |
| A tool error | Only the "Something went wrong" one, later |

More detail: [API errors](https://docs.lanesra.ai/api-keys-errors) on docs.lanesra.ai. Support: [docs.lanesra.ai/support](https://docs.lanesra.ai/support).
