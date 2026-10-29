"""Export daily visibility and competitive score for every tracked brand to CSV, for a warehouse or BI tool.

    export LANESRA_API_KEY=lns_live_your_key_here
    python export_history_csv.py --project acme --from 2026-09-01 --to 2026-09-30 --out history.csv

Without --from and --to it exports the project's whole life. One row per day and
brand. Days with no capture are left out rather than written as zero.
"""

import argparse
import csv
import sys

from lanesra import Lanesra, LanesraError

COLUMNS = ["project", "locale", "date", "brand", "visibility_pct", "competitive_score"]


def history_rows(history: dict):
    """One row per (day, brand) that has a value."""
    locale = history.get("locale") or ""
    for brand, visibility in history["brands"].items():
        scores = history["scores"].get(brand, [])
        for i, day in enumerate(history["dates"]):
            vis = visibility[i] if i < len(visibility) else None
            score = scores[i] if i < len(scores) else None
            if vis is None and score is None:
                continue
            yield {
                "project": history["project"],
                "locale": locale,
                "date": day,
                "brand": brand,
                "visibility_pct": vis,
                "competitive_score": score,
            }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", help="project slug; needed when the key reads several projects")
    parser.add_argument("--locale", help="market and language, such as en-US; default the project's primary one")
    parser.add_argument("--from", dest="start", help="first UTC day, yyyy-mm-dd")
    parser.add_argument("--to", dest="end", help="last UTC day, yyyy-mm-dd")
    parser.add_argument("--out", help="output file; default standard output")
    args = parser.parse_args()
    if bool(args.start) != bool(args.end):
        parser.error("give --from and --to together")

    history = Lanesra().call(
        "get_visibility_history",
        project=args.project,
        locale=args.locale,
        **({"from": args.start, "to": args.end} if args.start else {"period": "all_time"}),
    )

    out = open(args.out, "w", newline="") if args.out else sys.stdout
    try:
        writer = csv.DictWriter(out, fieldnames=COLUMNS)
        writer.writeheader()
        count = 0
        for row in history_rows(history):
            writer.writerow(row)
            count += 1
    finally:
        if args.out:
            out.close()
    print(f"Wrote {count} rows.", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except LanesraError as e:
        sys.exit(f"Lanesra: {e}")
