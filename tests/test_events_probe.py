import base64
import io
import json
from unittest.mock import patch
import unittest

import httpx

from events_probe import EVENT_NAME, EventsProbe, ProbeError, _callback_url, _parse_allowlist, _signature


class TestEventsProbe(unittest.TestCase):
    def setUp(self):
        self.secret = base64.b64encode(b"x" * 32).decode("ascii")
        self.calls = []

        def sender(url, secret, subscription_id, message_id, payload):
            self.calls.append((url, subscription_id, message_id, payload))
            if payload.get("type") == "verification":
                return httpx.Response(200, json={"challenge": payload["challenge"]})
            return httpx.Response(204)

        self.probe = EventsProbe(("*.openai.com",), sender=sender)

    @patch("events_probe._require_public_dns")
    def test_subscribe_verifies_and_delivers_one_redacted_event(self, _dns):
        result = self.probe.subscribe({
            "name": EVENT_NAME,
            "arguments": {},
            "delivery": {
                "mode": "webhook",
                "url": "https://events.openai.com/mcp/callback",
                "secret": "whsec_" + self.secret,
            },
        })
        self.assertTrue(result["id"].startswith("sub_probe_"))
        self.assertEqual(len(self.calls), 2)
        verification, event = self.calls
        self.assertEqual(verification[3]["type"], "verification")
        self.assertEqual(event[3]["name"], EVENT_NAME)
        self.assertEqual(event[3]["data"], {"status": "accepted"})
        self.assertNotIn("url", event[3])
        self.assertNotIn("secret", event[3])

    @patch("events_probe._require_public_dns")
    def test_unsubscribe_is_idempotent(self, _dns):
        params = {
            "name": EVENT_NAME,
            "arguments": {},
            "delivery": {
                "mode": "webhook",
                "url": "https://events.openai.com/mcp/callback",
                "secret": "whsec_" + self.secret,
            },
        }
        self.probe.subscribe(params)
        unsub = {
            "name": EVENT_NAME,
            "arguments": {},
            "delivery": {"mode": "webhook", "url": params["delivery"]["url"]},
        }
        self.assertEqual(self.probe.unsubscribe(unsub), {})
        self.assertEqual(self.probe.unsubscribe(unsub), {})

    def test_empty_allowlist_denies_callback_without_sending(self):
        probe = EventsProbe((), sender=lambda *args: self.fail("must not send"))
        with self.assertRaisesRegex(ProbeError, "callback denied"):
            probe.subscribe({
                "name": EVENT_NAME,
                "arguments": {},
                "delivery": {
                    "mode": "webhook",
                    "url": "https://events.openai.com/mcp/callback",
                    "secret": "whsec_" + self.secret,
                },
            })

    @patch("events_probe._require_public_dns")
    def test_label_boundary_and_port_policy(self, _dns):
        allowlist = _parse_allowlist("*.openai.com,chatgpt.example.com")
        self.assertEqual(_callback_url("https://events.openai.com/a", allowlist),
                         "https://events.openai.com/a")
        self.assertEqual(_callback_url("https://chatgpt.example.com/a", allowlist),
                         "https://chatgpt.example.com/a")
        for value in ("https://openai.com/a", "https://evil-openai.com/a",
                      "http://events.openai.com/a", "https://events.openai.com:444/a"):
            with self.assertRaisesRegex(ProbeError, "callback denied"):
                _callback_url(value, allowlist)

    def test_invalid_allowlist_form_is_rejected(self):
        for value in ("*", "**.openai.com", "https://openai.com", "openai.com:443"):
            with self.assertRaisesRegex(ProbeError, "invalid Dev probe allowlist"):
                _parse_allowlist(value)

    def test_signature_covers_message_id_timestamp_and_exact_body(self):
        secret = b"s" * 32
        first = _signature(secret, "msg_a", "1", b"{}")
        self.assertTrue(first.startswith("v1,"))
        self.assertNotEqual(first, _signature(secret, "msg_b", "1", b"{}"))
        self.assertNotEqual(first, _signature(secret, "msg_a", "2", b"{}"))
        self.assertNotEqual(first, _signature(secret, "msg_a", "1", b'{"x":1}'))

    def test_discovery_advertises_events_without_tools(self):
        response = self.probe.handle({"jsonrpc": "2.0", "id": 1, "method": "server/discover"})
        self.assertEqual(response["result"]["supportedVersions"], ["2026-07-28"])
        self.assertEqual(response["result"]["capabilities"], {"tools": {}, "events": {}})
        events = self.probe.handle({"jsonrpc": "2.0", "id": 2, "method": "events/list"})
        self.assertEqual(events["result"]["events"][0]["name"], EVENT_NAME)

        tools = self.probe.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
        self.assertEqual(tools["result"], {"tools": []})

    def test_trace_records_methods_and_outcomes_without_request_data(self):
        stderr = io.StringIO()
        marker = "private-callback-or-secret"
        with patch("sys.stderr", stderr):
            result = self.probe.handle({
                "jsonrpc": "2.0", "id": marker, "method": "server/discover",
                "params": {"untrusted": marker},
            })
            bad = self.probe.handle({
                "jsonrpc": "2.0", "id": marker, "method": "events/subscribe",
                "params": {"secret": marker, "url": marker},
            })
        self.assertIn("result", result)
        self.assertEqual(bad["error"]["code"], -32602)
        lines = [json.loads(line) for line in stderr.getvalue().splitlines()]
        self.assertEqual([(line["method"], line["outcome"]) for line in lines],
                         [("server/discover", "ok"), ("events/subscribe", "error")])
        self.assertNotIn(marker, stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
