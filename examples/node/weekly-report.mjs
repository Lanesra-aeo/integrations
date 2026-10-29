// A weekly AI-visibility summary: headline numbers, the top brands and the most cited sites.
//
//   export LANESRA_API_KEY=lns_live_your_key_here
//   export LANESRA_PROJECT=acme                  # only if your key reads several projects
//   export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/…   # optional
//   node weekly-report.mjs
//
// Without SLACK_WEBHOOK_URL the report is printed. The formatting is Slack's mrkdwn,
// which also reads fine as plain text.

import { pathToFileURL } from "node:url"
import { Lanesra } from "./lanesra.mjs"

const TOP_BRANDS = 5
const TOP_SOURCES = 5

const fmt = (value, suffix = "") => (value === null || value === undefined ? "n/a" : `${value}${suffix}`)

export function buildReport(overview, rankings, sources) {
  const own = overview.own ?? {}
  const captured = overview.capturedAt ? overview.capturedAt.slice(0, 10) : "not yet"
  const lines = [
    `*${overview.brand}: AI visibility*`,
    `Captured ${captured} over ${overview.answers} answers from ${overview.engines.join(", ") || "no engines yet"}.`,
    "",
    `• Competitive score: *${fmt(own.score)}*`,
    `• Visibility: *${fmt(own.visibility, "%")}*`,
    `• Share of voice: *${fmt(own.shareOfVoice, "%")}*`,
    `• Average position: *${fmt(own.avgPosition)}*`,
    `• Rank: *${fmt(overview.rankAmongTracked)}* of ${overview.trackedBrands} tracked brands`,
  ]
  if (overview.note) lines.push("", `_${overview.note}_`)

  lines.push("", "*Top brands by competitive score*")
  rankings.brands.forEach((b, i) => {
    // With `limit`, your own brand is added after the top brands when it ranks below them.
    const rank = i < TOP_BRANDS ? i + 1 : overview.rankAmongTracked
    if (i >= TOP_BRANDS) lines.push("…")
    lines.push(`${rank}. ${b.brand}${b.isOwn ? " (you)" : ""}: score ${fmt(b.score)}, visibility ${fmt(b.visibility, "%")}`)
  })

  lines.push("", "*Most cited sites*")
  for (const d of sources.domains) lines.push(`• ${d.domain}: cited in ${d.answersCiting} answers (${fmt(d.citedInPct, "%")})`)

  return lines.join("\n")
}

async function main() {
  const client = new Lanesra()
  const project = process.env.LANESRA_PROJECT // undefined is fine when the key reads one project

  const [overview, rankings, sources] = await Promise.all([
    client.call("get_visibility_overview", { project }),
    client.call("get_brand_rankings", { project, minMentions: 1, limit: TOP_BRANDS }),
    client.call("get_sources", { project, limit: TOP_SOURCES }),
  ])

  const report = buildReport(overview, rankings, sources)
  const webhook = process.env.SLACK_WEBHOOK_URL
  if (!webhook) {
    console.log(report)
    return
  }
  const res = await fetch(webhook, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: report }) })
  if (!res.ok) throw new Error(`Slack: HTTP ${res.status} ${await res.text()}`)
  console.log("Posted the report to Slack.")
}

// Run only when started directly, so the tests can import buildReport.
if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  await main().catch((e) => {
    console.error(`Lanesra: ${e.message}`)
    process.exit(1)
  })
}
