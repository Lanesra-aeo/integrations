"""Offline tests for the Python examples. No key and no network: a local stub server plays Lanesra.

    python -m unittest discover -s tests/python -v
"""

import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(ROOT / "examples" / "python"))

import export_history_csv  # noqa: E402
import lanesra  # noqa: E402
import visibility_alert  # noqa: E402
import weekly_report  # noqa: E402
from lanesra import Lanesra, LanesraHTTPError, LanesraRPCError, LanesraToolError, parse_body, tool_data  # noqa: E402


def fixture(name):
    return json.loads((FIXTURES / f"{name}.json").read_text())


def tool_result(data, is_error=False):
    text = data if isinstance(data, str) else json.dumps(data)
    result = {"content": [{"type": "text", "text": text}]}
    if is_error:
        result["isError"] = True
    return result


class Stub(BaseHTTPRequestHandler):
    """Answers like the Lanesra endpoint, choosing the case from the key and the tool name."""

    calls = []
    flaky_left = 0

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Stub.calls.append({"headers": dict(self.headers), "body": body})
        auth = self.headers.get("Authorization", "")
        tool = body.get("params", {}).get("name")
        rid = body.get("id")

        if auth == "Bearer lns_live_revoked":
            return self.reply(401, {"jsonrpc": "2.0", "error": {"code": -32001, "message": "Unauthorized: send a Lanesra key"}, "id": None})
        if auth == "Bearer lns_live_lapsed":
            error = {"code": -32002, "message": "Billing for this account has lapsed", "data": {"reason": "billing_lapsed"}}
            return self.reply(403, {"jsonrpc": "2.0", "error": error, "id": None})
        if tool == "flaky" and Stub.flaky_left > 0:
            Stub.flaky_left -= 1
            return self.reply(503, None, raw="<html>Service Unavailable</html>", content_type="text/html")
        if body.get("method") == "tools/list":
            return self.reply(200, {"jsonrpc": "2.0", "id": rid, "result": {"tools": [{"name": "get_visibility_overview"}]}})
        if tool == "rpc_error":
            return self.reply(200, {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "Invalid arguments"}})
        if tool == "tool_error":
            return self.reply(200, {"jsonrpc": "2.0", "id": rid, "result": tool_result("No project \"nope\" on this account", True)})
        if tool == "plain_json":
            return self.reply(200, {"jsonrpc": "2.0", "id": rid, "result": tool_result({"form": "json"})}, sse=False)
        if tool == "echo":
            return self.reply(200, {"jsonrpc": "2.0", "id": rid, "result": tool_result(body["params"]["arguments"])})
        # Everything else answers like the real server: one event-stream frame.
        return self.reply(200, {"jsonrpc": "2.0", "id": rid, "result": tool_result({"form": "sse", "tool": tool})})

    def reply(self, status, message, sse=True, raw=None, content_type=None):
        if raw is not None:
            payload = raw
        elif sse and status == 200:
            payload = f"event: message\ndata: {json.dumps(message)}\n\n"
            content_type = "text/event-stream"
        else:
            payload = json.dumps(message)
            content_type = content_type or "application/json"
        data = payload.encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type or "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


class StubServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
        cls.url = f"http://127.0.0.1:{cls.server.server_address[1]}/mcp"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        Stub.calls.clear()

    def client(self, key="lns_live_test", **kw):
        return Lanesra(api_key=key, url=self.url, **kw)


class ParsingTest(unittest.TestCase):
    def test_plain_json_body(self):
        self.assertEqual(parse_body('{"id":1}', "application/json"), [{"id": 1}])

    def test_event_stream_body(self):
        body = 'event: message\ndata: {"id":1,"result":{}}\n\n'
        self.assertEqual(parse_body(body, "text/event-stream"), [{"id": 1, "result": {}}])

    def test_event_stream_with_crlf_and_split_data_lines(self):
        body = 'event: message\r\ndata: {"id":1,\r\ndata: "result":{}}\r\n\r\n'
        self.assertEqual(parse_body(body, "text/event-stream"), [{"id": 1, "result": {}}])

    def test_tool_data_parses_json_text(self):
        self.assertEqual(tool_data(tool_result({"a": 1})), {"a": 1})

    def test_tool_data_returns_text_that_is_not_json(self):
        self.assertEqual(tool_data(tool_result("plain words")), "plain words")

    def test_tool_data_raises_on_is_error(self):
        with self.assertRaisesRegex(LanesraToolError, "pass one as"):
            tool_data(tool_result("This account tracks several brands - pass one as `project`", True))


class ClientTest(StubServerTest):
    def test_sends_the_required_headers(self):
        self.client().call("get_visibility_overview")
        headers = {k.lower(): v for k, v in Stub.calls[0]["headers"].items()}
        self.assertEqual(headers["authorization"], "Bearer lns_live_test")
        self.assertEqual(headers["accept"], "application/json, text/event-stream")
        self.assertEqual(headers["content-type"], "application/json")

    def test_reads_an_event_stream_reply(self):
        self.assertEqual(self.client().call("get_sources"), {"form": "sse", "tool": "get_sources"})

    def test_reads_a_plain_json_reply(self):
        self.assertEqual(self.client().call("plain_json"), {"form": "json"})

    def test_drops_arguments_left_as_none(self):
        self.assertEqual(self.client().call("echo", project=None, limit=5), {"limit": 5})

    def test_lists_tools(self):
        self.assertEqual(self.client().list_tools(), [{"name": "get_visibility_overview"}])

    def test_401_raises_with_status_and_code(self):
        with self.assertRaises(LanesraHTTPError) as cm:
            self.client(key="lns_live_revoked").call("get_visibility_overview")
        self.assertEqual((cm.exception.status, cm.exception.code), (401, -32001))

    def test_403_carries_the_reason(self):
        with self.assertRaises(LanesraHTTPError) as cm:
            self.client(key="lns_live_lapsed").call("get_visibility_overview")
        self.assertEqual((cm.exception.status, cm.exception.reason), (403, "billing_lapsed"))

    def test_json_rpc_error_raises(self):
        with self.assertRaises(LanesraRPCError) as cm:
            self.client().call("rpc_error")
        self.assertEqual(cm.exception.code, -32602)

    def test_tool_error_raises_with_its_message(self):
        with self.assertRaisesRegex(LanesraToolError, 'No project "nope"'):
            self.client().call("tool_error")

    def test_retries_a_503_then_succeeds(self):
        Stub.flaky_left = 1
        with mock.patch.object(lanesra.time, "sleep") as sleep:
            self.assertEqual(self.client(retries=2).call("flaky")["tool"], "flaky")
        sleep.assert_called_once()

    def test_gives_up_after_the_last_retry(self):
        Stub.flaky_left = 5
        with mock.patch.object(lanesra.time, "sleep"), self.assertRaises(LanesraHTTPError) as cm:
            self.client(retries=1).call("flaky")
        self.assertEqual(cm.exception.status, 503)

    def test_missing_key_is_reported(self):
        with mock.patch.dict("os.environ", {}, clear=True), self.assertRaisesRegex(lanesra.LanesraError, "LANESRA_API_KEY"):
            Lanesra(url=self.url)


class ExamplesTest(unittest.TestCase):
    def test_weekly_report_from_real_shapes(self):
        report = weekly_report.build_report(fixture("overview"), fixture("rankings"), fixture("sources"))
        self.assertIn("*Acme: AI visibility*", report)
        self.assertIn("Visibility: *78.3%*", report)
        self.assertIn("1. Acme (you)", report)
        self.assertIn("site-1.example: cited in 11 answers", report)

    def test_weekly_report_numbers_your_brand_by_its_rank_when_it_is_added_below_the_top(self):
        overview = dict(fixture("overview"), rankAmongTracked=9)
        rankings = fixture("rankings")
        others = [dict(b, isOwn=False, brand=f"Brand {i}") for i, b in enumerate(rankings["brands"] * 2)][:5]
        own = dict(rankings["brands"][0], isOwn=True)
        report = weekly_report.build_report(overview, {"brands": others + [own]}, fixture("sources"))
        self.assertIn("…\n9. Acme (you)", report)

    def test_alert_compares_the_two_latest_capture_days(self):
        history = fixture("history")
        pair = visibility_alert.last_two_captured(history["dates"], history["brands"]["Acme"])
        self.assertEqual([d for d, _ in pair], ["2026-08-08", "2026-08-10"])

    def test_alert_needs_two_capture_days(self):
        self.assertIsNone(visibility_alert.last_two_captured(["2026-08-01", "2026-08-02"], [None, 50.0]))

    def test_csv_rows_skip_days_without_a_capture(self):
        rows = list(export_history_csv.history_rows(fixture("history")))
        self.assertTrue(rows)
        self.assertTrue(all(r["visibility_pct"] is not None or r["competitive_score"] is not None for r in rows))
        self.assertEqual({r["date"] for r in rows if r["brand"] == "Acme"}, {"2026-08-08", "2026-08-10"})


if __name__ == "__main__":
    unittest.main()
