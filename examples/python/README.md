# Python examples

Python 3.10 or later. Everything except `mcp_sdk.py` uses only the standard library, so there is nothing to install.

```bash
cd examples/python
export LANESRA_API_KEY=lns_live_your_key_here
python quickstart.py
```

| File | What it does |
| --- | --- |
| [`lanesra.py`](lanesra.py) | The client: one JSON-RPC call per `POST`, both response forms, errors as exceptions, retries on `502`, `503` and `504` |
| [`quickstart.py`](quickstart.py) | Lists the projects your key reads and prints each one's headline numbers |
| [`weekly_report.py`](weekly_report.py) | Headline numbers, top brands and most cited sites, printed or posted to Slack |
| [`visibility_alert.py`](visibility_alert.py) | Compares your visibility on the last two capture days and exits with status 1 on a drop |
| [`export_history_csv.py`](export_history_csv.py) | Writes daily visibility and competitive score for every brand to CSV |
| [`mcp_sdk.py`](mcp_sdk.py) | The first call through the official MCP Python SDK (`pip install -r requirements-sdk.txt`) |

## Settings

| Variable | Used by | What it is |
| --- | --- | --- |
| `LANESRA_API_KEY` | all | Your key, `lns_live_…`. Required |
| `LANESRA_PROJECT` | report, alert | A project slug. Needed only when the key reads several projects |
| `SLACK_WEBHOOK_URL` | report, alert | A Slack incoming webhook. Without it, output is printed |
| `ALERT_DROP_POINTS` | alert | The drop in percentage points that triggers the alert. Default 5 |
| `ALERT_LOOKBACK_DAYS` | alert | How many days back to look for the two latest capture days. Default 30 |

## Using the client

```python
from lanesra import Lanesra, LanesraHTTPError, LanesraToolError

client = Lanesra()

try:
    rankings = client.call("get_brand_rankings", project="acme", locale="en-US", limit=10)
except LanesraHTTPError as e:
    # 401: the key is wrong or was revoked. 403: see e.reason, such as billing_lapsed.
    raise SystemExit(f"Lanesra refused the key: {e} (reason: {e.reason})")
except LanesraToolError as e:
    # The tool ran but could not answer. The message is written for a person.
    raise SystemExit(str(e))

for brand in rankings["brands"]:
    print(brand["brand"], brand["score"], brand["visibility"])
```

Arguments left as `None` are not sent, so optional settings can be passed straight through. `from` is a Python keyword, so pass a date range as `**{"from": "2026-10-01", "to": "2026-10-28"}`.
