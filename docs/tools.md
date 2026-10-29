# Tools

Every tool the Lanesra endpoint offers, with its arguments. For the full description of each result, see [MCP tools](https://docs.lanesra.ai/mcp-tools) on docs.lanesra.ai. For the exact argument schemas, call `tools/list`.

Every tool that reads a project takes an optional `project` slug. You need it only when your key reads more than one project. Tools marked **period** also take `locale`, `period`, `from` and `to`, described in [Making requests](making-requests.md#market-language-and-period).

## Read tools

| Tool | Arguments | Returns |
| --- | --- | --- |
| `list_projects` | none | The account, and each project's `slug`, `name`, markets and languages (`locales`) and business areas |
| `get_visibility_overview` | `project`, period | Your headline numbers: competitive score, visibility, share of voice, average position and mentions (`own`), Recognition, how often you are named as an alternative to each competitor, and your rank among tracked brands. **Start here.** |
| `get_brand_rankings` | `project`, period, `minMentions`, `limit` | Every tracked brand ranked by competitive score, with visibility, share of voice, position, sentiment, NPS and mentions (`brands`) |
| `get_visibility_history` | `project`, period | Visibility and competitive score per UTC day for every tracked brand: `dates`, `brands` and `scores`, each brand's list aligned with `dates` |
| `get_prompts` | `project`, period | How your brand does on each tracked prompt |
| `get_sources` | `project`, period, `limit` (1 to 100, default 25) | The sites and pages AI cites, most cited first, with who wins the answers that cite them |
| `get_gap_analysis` | `project`, period | The prompts each side leads, and the content findings that explain why |
| `get_actions` | `project`, period, `kind` (`earned` or `owned`), `limit` | What to do next: the dashboard's Outreach and Your website actions, ranked |
| `get_cited_not_named` | `project`, period | How often each brand's own site is cited in answers that never name the brand |
| `get_capture_status` | `project` | Whether a capture is running and how the last one ended |
| `get_ai_referrals` | `project`, `locale`, `days` (7, 30 or 90) | Visits AI assistants send to your site and what they convert, from Google Analytics. Offered where AI referrals is turned on |
| `get_agent_access` | `project` | Whether each AI engine can reach your website, from the latest check |
| `get_webmcp_report` | `project` | What your site and competitors' sites offer AI agents through WebMCP. Offered where Agent experience is turned on |
| `get_brand_archetype` | `project` | How AI engines read your brand's personality. Offered where Brand Archetype is turned on |
| `get_public_index` | `limit` (1 to 100, default 25) | The public Lanesra AI Visibility Index, comparable across companies |
| `explain_metric` | `metric` (optional) | What a metric means and how it is computed. With no argument, every metric |

## Chart tools

These return the same data as the read tool they draw from, as an interactive chart for clients that show one. From a script, call the read tool instead.

| Tool | Draws from |
| --- | --- |
| `show_visibility_chart` | `get_brand_rankings` |
| `show_visibility_history_chart` | `get_visibility_history` |
| `show_sources_chart` | `get_sources` |
| `show_ai_referrals_chart` | `get_ai_referrals` |

## Change tools

Change tools are offered only when the key's role makes changes, and only the ones that role allows. A Viewer key never sees them. Every change is recorded with the key that made it. See [Change tools](https://docs.lanesra.ai/mcp-tools#change-tools) for each one's rules.

| Area | Tools |
| --- | --- |
| Prompts | `add_prompts`, `update_prompts`, `pause_prompts`, `resume_prompts` |
| Competitors | `add_competitor`, `update_competitor` |
| Captures | `plan_capture`, `start_capture`, `cancel_capture` |
| Briefs | `generate_brief` |
| Brand Archetype | `start_archetype_setup`, `set_declared_archetype`, `add_brand_probes`, `add_custom_probe`, `remove_brand_probe`, `generate_archetype_brief` |

**Captures spend credits.** `start_capture` only starts a capture that `plan_capture` quoted in the last 10 minutes, exactly as quoted. Show the quote to a person before starting it.

**Changes are rate limited.** A key or app can make 60 changes an hour, and a company 500 a day. Further limits apply per project: 100 prompts added and 50 paused a day, 10 briefs a day, and 3 captures started a day, of at most 500 units each. A refused call says when to try again.

## Example: rankings for one market over a range

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "get_brand_rankings",
    "arguments": { "project": "acme", "locale": "en-US", "from": "2026-10-01", "to": "2026-10-28", "minMentions": 1, "limit": 10 }
  }
}
```

The result holds the header fields, then `totalBrands` and `brands`. Each brand has `brand`, `isOwn`, `score`, `visibility`, `shareOfVoice`, `avgPosition`, `sentiment`, `mentions` and its NPS fields. Percentages are numbers from 0 to 100.
