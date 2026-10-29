"""A minimal client for the Lanesra MCP endpoint, using only the Python standard library.

    from lanesra import Lanesra

    client = Lanesra()                      # reads LANESRA_API_KEY
    overview = client.call("get_visibility_overview")
    print(overview["capturedAt"], overview["own"]["visibility"])

Every call is one JSON-RPC request in a POST. The server answers with plain JSON
or with a single Server-Sent Events frame; both are handled here. A tool's data
is a JSON string inside result.content[0].text, which call() parses for you.
"""

from __future__ import annotations

import itertools
import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

DEFAULT_URL = "https://app.lanesra.ai/mcp"

# Worth retrying: the server or a proxy in front of it was briefly unavailable.
RETRY_STATUSES = {502, 503, 504}


class LanesraError(Exception):
    """Base class for every error this client raises."""


class LanesraHTTPError(LanesraError):
    """The request was refused before any tool ran: 401, 403, 405 and the like.

    `reason` is set on a 403 (no_plan, billing_lapsed, company_suspended or
    user_suspended). Retrying with the same key never clears a 401 or 403.
    """

    def __init__(self, status: int, message: str, code: int | None = None, reason: str | None = None):
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.code = code
        self.reason = reason


class LanesraRPCError(LanesraError):
    """A JSON-RPC error returned with HTTP 200, such as an unknown method or invalid arguments."""

    def __init__(self, code: int | None, message: str):
        super().__init__(f"JSON-RPC error {code}: {message}")
        self.code = code


class LanesraToolError(LanesraError):
    """The tool ran and could not answer. The message is written for a person to read."""


def parse_body(body: str, content_type: str = "") -> list[dict]:
    """Every JSON-RPC message in a response body, whichever of the two forms it came in."""
    if "text/event-stream" not in content_type and body.lstrip().startswith(("{", "[")):
        parsed = json.loads(body)
        return parsed if isinstance(parsed, list) else [parsed]

    messages = []
    # Events are separated by a blank line; an event's data may span several "data:" lines.
    for event in body.replace("\r\n", "\n").split("\n\n"):
        data = [line[5:].removeprefix(" ") for line in event.split("\n") if line.startswith("data:")]
        if data:
            messages.append(json.loads("\n".join(data)))
    return messages


def tool_data(result: dict) -> Any:
    """The data a tool returned: its text parsed as JSON, or the text itself when it is not JSON."""
    content = result.get("content") or []
    text = "\n".join(c.get("text", "") for c in content if c.get("type") == "text")
    if result.get("isError"):
        raise LanesraToolError(text or "The tool returned an error with no message.")
    try:
        return json.loads(text)
    except ValueError:
        return text


class Lanesra:
    def __init__(self, api_key: str | None = None, url: str | None = None, timeout: float = 60, retries: int = 2):
        self.api_key = api_key or os.environ.get("LANESRA_API_KEY")
        if not self.api_key:
            raise LanesraError("No API key: set LANESRA_API_KEY, or pass api_key. Create one under Integrations → API keys.")
        self.url = url or os.environ.get("LANESRA_MCP_URL") or DEFAULT_URL
        self.timeout = timeout
        self.retries = retries
        self._ids = itertools.count(1)

    def call(self, tool: str, **arguments: Any) -> Any:
        """Call one tool and return its parsed data. Arguments left as None are not sent."""
        args = {k: v for k, v in arguments.items() if v is not None}
        return tool_data(self.request("tools/call", {"name": tool, "arguments": args}))

    def list_tools(self) -> list[dict]:
        """Every tool this key can use, with its description and argument schema."""
        return self.request("tools/list")["tools"]

    def request(self, method: str, params: dict | None = None) -> dict:
        """Send one JSON-RPC request and return its `result`."""
        request_id = next(self._ids)
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            payload["params"] = params

        status, content_type, body = self._post(json.dumps(payload).encode())
        try:
            messages = parse_body(body, content_type) if body.strip() else []
        except ValueError:
            # Not JSON-RPC at all, such as a proxy's HTML error page.
            if status < 400:
                raise LanesraError(f"Unreadable response (HTTP {status}): {body[:500]}") from None
            messages = []

        if status >= 400:
            error = next((m["error"] for m in messages if "error" in m), {})
            data = error.get("data") or {}
            raise LanesraHTTPError(status, error.get("message") or body[:500], error.get("code"), data.get("reason"))

        reply = next((m for m in messages if m.get("id") == request_id), None)
        if reply is None:
            raise LanesraError(f"No response to request {request_id} in the body: {body[:500]}")
        if "error" in reply:
            raise LanesraRPCError(reply["error"].get("code"), reply["error"].get("message", ""))
        return reply["result"]

    def _post(self, data: bytes) -> tuple[int, str, str]:
        req = urllib.request.Request(
            self.url,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "User-Agent": "lanesra-integrations-python/1.0",
            },
        )
        for attempt in range(self.retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as res:
                    return res.status, res.headers.get("Content-Type", ""), res.read().decode("utf-8")
            except urllib.error.HTTPError as e:
                if e.code not in RETRY_STATUSES or attempt == self.retries:
                    return e.code, e.headers.get("Content-Type", ""), e.read().decode("utf-8", "replace")
            except (urllib.error.URLError, TimeoutError):
                if attempt == self.retries:
                    raise
            time.sleep(2**attempt)
        raise AssertionError("unreachable")
