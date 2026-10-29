"""A weekly AI-visibility summary: headline numbers, the top brands and the most cited sites.

    export LANESRA_API_KEY=lns_live_your_key_here
    export LANESRA_PROJECT=acme                  # only if your key reads several projects
    export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/…   # optional
    python weekly_report.py

Without SLACK_WEBHOOK_URL the report is printed. The formatting is Slack's mrkdwn,
which also reads fine as plain text.
"""

import os
import sys

from lanesra import Lanesra, LanesraError
from notify import post_to_slack

TOP_BRANDS = 5
TOP_SOURCES = 5


def fmt(value, suffix=""):
    return "n/a" if value is None else f"{value}{suffix}"


def build_report(overview: dict, rankings: dict, sources: dict) -> str:
    own = overview.get("own") or {}
    captured = overview["capturedAt"][:10] if overview.get("capturedAt") else "not yet"

    lines = [
        f"*{overview['brand']}: AI visibility*",
        f"Captured {captured} over {overview['answers']} answers from {', '.join(overview['engines']) or 'no engines yet'}.",
        "",
        f"• Competitive score: *{fmt(own.get('score'))}*",
        f"• Visibility: *{fmt(own.get('visibility'), '%')}*",
        f"• Share of voice: *{fmt(own.get('shareOfVoice'), '%')}*",
        f"• Average position: *{fmt(own.get('avgPosition'))}*",
        f"• Rank: *{fmt(overview.get('rankAmongTracked'))}* of {overview.get('trackedBrands')} tracked brands",
    ]
    if overview.get("note"):
        lines += ["", f"_{overview['note']}_"]

    lines += ["", "*Top brands by competitive score*"]
    for i, b in enumerate(rankings["brands"], start=1):
        you = " (you)" if b["isOwn"] else ""
        # With `limit`, your own brand is added after the top brands when it ranks below them.
        rank = i if i <= TOP_BRANDS else overview.get("rankAmongTracked")
        if i > TOP_BRANDS:
            lines.append("…")
        lines.append(f"{rank}. {b['brand']}{you}: score {fmt(b['score'])}, visibility {fmt(b['visibility'], '%')}")

    lines += ["", "*Most cited sites*"]
    for d in sources["domains"]:
        lines.append(f"• {d['domain']}: cited in {d['answersCiting']} answers ({fmt(d['citedInPct'], '%')})")

    return "\n".join(lines)


def main():
    client = Lanesra()
    project = os.environ.get("LANESRA_PROJECT")  # None is fine when the key reads one project

    overview = client.call("get_visibility_overview", project=project)
    rankings = client.call("get_brand_rankings", project=project, minMentions=1, limit=TOP_BRANDS)
    sources = client.call("get_sources", project=project, limit=TOP_SOURCES)

    report = build_report(overview, rankings, sources)
    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if webhook:
        post_to_slack(webhook, report)
        print("Posted the report to Slack.")
    else:
        print(report)


if __name__ == "__main__":
    try:
        main()
    except LanesraError as e:
        sys.exit(f"Lanesra: {e}")
