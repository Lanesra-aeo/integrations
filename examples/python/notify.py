"""Post a message to Slack through an incoming webhook, using only the standard library."""

import json
import urllib.request


def post_to_slack(webhook_url: str, text: str) -> None:
    """Send `text` (Slack mrkdwn) to the channel the webhook belongs to."""
    req = urllib.request.Request(
        webhook_url,
        data=json.dumps({"text": text}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        res.read()
