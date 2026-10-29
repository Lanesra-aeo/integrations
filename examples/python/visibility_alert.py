"""Flag a drop in your brand's AI visibility between its two most recent capture days.

    export LANESRA_API_KEY=lns_live_your_key_here
    export LANESRA_PROJECT=acme                  # only if your key reads several projects
    export ALERT_DROP_POINTS=5                   # optional, percentage points (default 5)
    export ALERT_LOOKBACK_DAYS=30                # optional, how far back to look for capture days
    export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/…   # optional
    python visibility_alert.py

Exits with status 1 when visibility fell by at least ALERT_DROP_POINTS, so a
scheduler or CI job can act on it. Run it once a day, after your project's daily capture.
"""

import os
import sys
from datetime import datetime, timedelta, timezone

from lanesra import Lanesra, LanesraError
from notify import post_to_slack

LOOKBACK_DAYS = int(os.environ.get("ALERT_LOOKBACK_DAYS", "30"))


def last_two_captured(dates: list, values: list):
    """The two most recent days that have a value. Days with no capture are None, not zero."""
    captured = [(d, v) for d, v in zip(dates, values) if v is not None]
    return captured[-2:] if len(captured) >= 2 else None


def main():
    client = Lanesra()
    project = os.environ.get("LANESRA_PROJECT")
    threshold = float(os.environ.get("ALERT_DROP_POINTS", "5"))

    overview = client.call("get_visibility_overview", project=project)
    brand = overview["brand"]

    today = datetime.now(timezone.utc).date()  # capture days are UTC days
    history = client.call(
        "get_visibility_history",
        project=project,
        **{"from": (today - timedelta(days=LOOKBACK_DAYS)).isoformat(), "to": today.isoformat()},
    )
    series = history["brands"].get(brand)
    if series is None:
        sys.exit(f"No history for {brand!r}. Brands in the history: {', '.join(history['brands'])}")

    pair = last_two_captured(history["dates"], series)
    if pair is None:
        print(f"{brand}: fewer than two capture days in the last {LOOKBACK_DAYS} days, nothing to compare yet.")
        return

    (prev_day, prev), (last_day, last) = pair
    change = round(last - prev, 1)
    summary = f"{brand} visibility: {prev:.1f}% on {prev_day} → {last:.1f}% on {last_day} ({change:+} points)."
    print(summary)

    if change <= -threshold:
        message = f":warning: AI visibility dropped. {summary}"
        webhook = os.environ.get("SLACK_WEBHOOK_URL")
        if webhook:
            post_to_slack(webhook, message)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except LanesraError as e:
        sys.exit(f"Lanesra: {e}")
