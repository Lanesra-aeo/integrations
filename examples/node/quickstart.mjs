// List the projects your key reads, and print each one's headline numbers.
//
//   export LANESRA_API_KEY=lns_live_your_key_here
//   node quickstart.mjs

import { Lanesra, LanesraToolError } from "./lanesra.mjs"

/** A metric as text. null means it could not be computed, which is not the same as zero. */
const fmt = (value, suffix = "") => (value === null || value === undefined ? "n/a" : `${value}${suffix}`)

const client = new Lanesra()

const listing = await client.call("list_projects")
if (listing.projects.length === 0) {
  console.log(listing.note ?? "This key reads no projects.")
  process.exit(0)
}

for (const { slug } of listing.projects) {
  let overview
  try {
    overview = await client.call("get_visibility_overview", { project: slug })
  } catch (e) {
    // For example a project whose first capture has not finished yet.
    if (e instanceof LanesraToolError) {
      console.log(`${slug}: ${e.message}`)
      continue
    }
    throw e
  }

  const own = overview.own ?? {}
  console.log(`${overview.brand} (${slug})`)
  console.log(`  captured        ${overview.capturedAt ?? "not yet"}, over ${overview.answers} answers`)
  console.log(`  engines         ${overview.engines.join(", ")}`)
  console.log(`  score           ${fmt(own.score)}`)
  console.log(`  visibility      ${fmt(own.visibility, "%")}`)
  console.log(`  share of voice  ${fmt(own.shareOfVoice, "%")}`)
  console.log(`  avg position    ${fmt(own.avgPosition)}`)
  console.log(`  rank            ${fmt(overview.rankAmongTracked)} of ${overview.trackedBrands}`)
  if (overview.note) console.log(`  note            ${overview.note}`)
}
