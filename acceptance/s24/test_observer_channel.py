"""Shared-key channel controls; public unit keys, no host/credential/route action."""
import asyncio
import base64
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import observer_channel as channel
from parent_contract import Hold, STAGES, decode, encode

UNIT_KEY = bytes(range(32))  # Public test material, never an operator credential.


class ChannelChecks(unittest.TestCase):
    def setUp(self):
        self.binding = dict(attempt="S24-unit-attempt", binding="a" * 64,
                            producer="UnitHost", role="host-memory")
        self.records = []
        self.calls = []
        self.client_time, self.server_time = 100.0, 9000.0

    def record(self, direction, raw):
        self.records.append((direction, raw))

    def client_clock(self):
        return self.client_time

    def server_clock(self):
        return self.server_time

    async def provider(self, stage, nonce):
        self.calls.append((stage, nonce))
        return {"nested": [1, {"keep": True, "null": None}], "unit": "synthetic"}

    def pair(self, *, mutate=None, provider=None, record=None):
        responder = channel.ObserverResponder(provider or self.provider, UNIT_KEY,
            **self.binding, record=self.record, clock=self.server_clock)

        async def exchange(raw):
            response = await responder.respond(raw)
            return mutate(raw, response) if mutate else response

        client = channel.ObserverClient(exchange, UNIT_KEY, **self.binding,
                                       record=record or self.record, clock=self.client_clock)
        return client, responder

    def assert_closed(self, client):
        count = len(self.calls)
        with self.assertRaises(Hold):
            asyncio.run(client.observe(STAGES[0]))
        self.assertEqual(len(self.calls), count)
        self.assertTrue(client.held)

    def test_all_44_stages_deep_payload_and_scoped_proof(self):
        client, server = self.pair()

        async def run():
            for index, stage in enumerate(STAGES):
                result = await client.observe(stage)
                self.assertEqual(result["payload"], {"nested": [1, {"keep": True, "null": None}],
                                                      "unit": "synthetic"})
                proof = result["message_proof"]
                self.assertTrue(proof["message_mac_verified"])
                self.assertEqual(proof["sequence"], index + 1)
                for key in ("host_identity_proved", "encrypted_carrier_proved",
                            "approval_authenticated", "raw_wire_capture"):
                    self.assertIs(proof[key], False)
        asyncio.run(run())
        self.assertEqual((len(self.calls), client.sequence, server.sequence), (44, 44, 44))
        self.assertEqual(len(client.nonces), 44)
        self.assertEqual(len(self.records), 44 * 4)
        with self.assertRaises(Hold):
            asyncio.run(client.observe(STAGES[-1]))
        self.assertTrue(client.held)

    def test_different_clock_origins_do_not_establish_clock_parity(self):
        client, _ = self.pair()
        result = asyncio.run(client.observe(STAGES[0]))
        self.assertEqual(result["message_proof"]["round_trip_seconds"], 0)
        self.assertNotEqual(self.client_time, self.server_time)

    def test_modified_payload_without_new_mac_is_rejected(self):
        def mutate(request, response):
            value = decode(response)
            value["message"]["payload"]["unit"] = "tampered"
            return encode(value)
        client, _ = self.pair(mutate=mutate)
        with self.assertRaisesRegex(Hold, "MAC mismatch"):
            asyncio.run(client.observe(STAGES[0]))
        self.assert_closed(client)

    def test_valid_mac_wrong_attempt_binding_producer_role_stage_sequence_nonce(self):
        changes = ({"attempt": "other"}, {"binding": "b" * 64}, {"producer": "OtherHost"},
                   {"role": "guest-resources"}, {"stage": STAGES[1]}, {"seq": 2},
                   {"nonce": "0" * 64}, {"direction": "request"})
        for change in changes:
            with self.subTest(change=change):
                def mutate(request, response):
                    message = decode(response)["message"]
                    message.update(change)
                    return channel.signed(UNIT_KEY, message)
                client, _ = self.pair(mutate=mutate)
                with self.assertRaises(Hold):
                    asyncio.run(client.observe(STAGES[0]))
                self.assertTrue(client.held)

    def test_wrong_key_or_unsigned_request_never_calls_provider(self):
        client, server = self.pair()

        async def steal(raw):
            self.request = raw
            raise Hold("unit stop before exchange")
        client.exchange = steal
        with self.assertRaises(Hold):
            asyncio.run(client.observe(STAGES[0]))
        message = decode(self.request)["message"]
        for raw in (channel.signed(b"x" * 32, message), encode({"message": message})):
            _, server = self.pair()
            with self.assertRaises(Hold):
                asyncio.run(server.respond(raw))
            self.assertTrue(server.held)
        self.assertEqual(self.calls, [])

    def test_reflected_signed_request_is_not_a_response(self):
        client, _ = self.pair()
        async def reflect(raw):
            return raw
        client.exchange = reflect
        with self.assertRaisesRegex(Hold, "binding/direction"):
            asyncio.run(client.observe(STAGES[0]))
        self.assert_closed(client)

    def test_response_replay_and_reused_nonce_are_blocked(self):
        client, server = self.pair()
        asyncio.run(client.observe(STAGES[0], nonce="c" * 64))
        request = [raw for direction, raw in self.records if direction == "request"][0]
        with self.assertRaisesRegex(Hold, "sequence/stage/replay"):
            asyncio.run(server.respond(request))
        count = len(self.calls)
        with self.assertRaisesRegex(Hold, "nonce reuse"):
            asyncio.run(client.observe(STAGES[1], nonce="c" * 64))
        self.assertEqual(len(self.calls), count)
        self.assert_closed(client)

    def test_old_response_cannot_answer_new_challenge(self):
        client, _ = self.pair()
        asyncio.run(client.observe(STAGES[0]))
        old = [raw for direction, raw in self.records if direction == "response"][-1]
        async def replay(raw):
            return old
        client.exchange = replay
        with self.assertRaises(Hold):
            asyncio.run(client.observe(STAGES[1]))
        self.assert_closed(client)

    def test_stale_round_trip_and_backwards_clock_hold(self):
        for backwards in (False, True):
            with self.subTest(backwards=backwards):
                def mutate(request, response):
                    self.client_time += -1 if backwards else channel.FRESHNESS_SECONDS + 0.01
                    return response
                client, _ = self.pair(mutate=mutate)
                with self.assertRaises(Hold):
                    asyncio.run(client.observe(STAGES[0]))
                self.assertTrue(client.held)

    def test_slow_or_failed_provider_consumes_request_without_retry(self):
        async def failed(stage, nonce):
            self.calls.append((stage, nonce))
            raise OSError("unit provider unavailable")
        client, server = self.pair(provider=failed)
        with self.assertRaises(OSError):
            asyncio.run(client.observe(STAGES[0]))
        self.assertEqual((len(self.calls), server.sequence), (1, 1))
        self.assertTrue(server.held)
        self.assert_closed(client)
        async def slow(stage, nonce):
            self.server_time += 1.1
            return {}
        client, server = self.pair(provider=slow)
        with self.assertRaisesRegex(Hold, "duration/shape"):
            asyncio.run(client.observe(STAGES[0]))
        self.assertTrue(server.held)
        self.assert_closed(client)

    def test_cancelled_exchange_latches_client(self):
        client, _ = self.pair()
        async def cancelled(raw):
            raise asyncio.CancelledError()
        client.exchange = cancelled
        with self.assertRaises(asyncio.CancelledError):
            asyncio.run(client.observe(STAGES[0]))
        self.assert_closed(client)

    def test_actual_cooperative_timeouts_latch_without_restarting_a_provider(self):
        async def stalled(*args):
            self.calls.append("one-stalled-call")
            await asyncio.Event().wait()
        client, _ = self.pair()
        client.exchange = stalled
        # Shorter unit-only bounds exercise cancellation without changing source limits.
        with patch.object(channel, "FRESHNESS_SECONDS", 0.01), self.assertRaises(TimeoutError):
            asyncio.run(client.observe(STAGES[0]))
        self.assert_closed(client)
        client, server = self.pair(provider=stalled)
        with patch.object(channel, "PRODUCER_SECONDS", 0.01), self.assertRaises(TimeoutError):
            asyncio.run(client.observe(STAGES[0]))
        self.assertTrue(server.held)
        self.assert_closed(client)
        self.assertEqual(len(self.calls), 2)

    def test_concurrent_exchange_latches_both_pending_and_next_use(self):
        client, _ = self.pair()
        async def run():
            entered, release = asyncio.Event(), asyncio.Event()
            original = client.exchange
            async def waiting(raw):
                entered.set()
                await release.wait()
                return await original(raw)
            client.exchange = waiting
            first = asyncio.create_task(client.observe(STAGES[0]))
            await entered.wait()
            with self.assertRaisesRegex(Hold, "concurrent"):
                await client.observe(STAGES[0])
            release.set()
            with self.assertRaisesRegex(Hold, "held during exchange"):
                await first
        asyncio.run(run())
        self.assert_closed(client)

    def test_recorder_failure_prevents_dispatch_and_acceptance(self):
        def failed(direction, raw):
            raise OSError("unit recorder failed")
        client, _ = self.pair(record=failed)
        with self.assertRaises(OSError):
            asyncio.run(client.observe(STAGES[0]))
        self.assertEqual(self.calls, [])
        self.assert_closed(client)
        def fail_response(direction, raw):
            if direction == "response":
                raise OSError("unit response evidence failed")
            self.record(direction, raw)
        client, server = self.pair(record=fail_response)
        with self.assertRaises(OSError):
            asyncio.run(client.observe(STAGES[0]))
        self.assertEqual((len(self.calls), client.sequence, server.sequence), (1, 0, 1))
        self.assert_closed(client)

    def test_concurrent_responder_never_collects_a_second_sample(self):
        async def run():
            entered, release = asyncio.Event(), asyncio.Event()
            async def provider(stage, nonce):
                self.calls.append((stage, nonce))
                entered.set()
                await release.wait()
                return {}
            client, server = self.pair(provider=provider)
            request = channel.signed(UNIT_KEY, {"v": 1, "direction": "request",
                **self.binding, "seq": 1, "stage": STAGES[0], "nonce": "c" * 64,
                "payload": {}, "sample_seconds": 0})
            first = asyncio.create_task(server.respond(request))
            await entered.wait()
            with self.assertRaisesRegex(Hold, "concurrent"):
                await server.respond(request)
            release.set()
            with self.assertRaisesRegex(Hold, "held during collection"):
                await first
            self.assertEqual(len(self.calls), 1)
            self.assertTrue(server.held)
        asyncio.run(run())

    def test_size_budget_duplicate_json_keys_and_nonfinite_values_rejected(self):
        changes = (
            lambda raw: raw[:-1] + b' ,"mac_sha256":"' + b"0" * 64 + b'"}\n',
            lambda raw: b'{"message":{},"message":{},"mac_sha256":"' + b"0" * 64 + b'"}\n',
            lambda raw: b'{"message":NaN}\n',
            lambda raw: b"x" * 65537,
        )
        for mutation in changes:
            with self.subTest(mutation=mutation):
                client, _ = self.pair(mutate=lambda request, reply: mutation(reply))
                with self.assertRaises(Hold):
                    asyncio.run(client.observe(STAGES[0]))
                self.assertTrue(client.held)
        client, _ = self.pair()
        with patch.object(channel, "BYTE_LIMIT", 1), self.assertRaises(Hold):
            asyncio.run(client.observe(STAGES[0]))
        self.assertTrue(client.held)

    def test_bad_metadata_and_duration_types_even_with_valid_mac(self):
        for update in ({"seq": True}, {"v": True}, {"sample_seconds": True},
                       {"sample_seconds": 1.01}, {"payload": []}, {"nonce": "not-a-nonce"}):
            with self.subTest(update=update):
                def mutate(request, reply):
                    message = decode(reply)["message"]
                    message.update(update)
                    return channel.signed(UNIT_KEY, message)
                client, _ = self.pair(mutate=mutate)
                with self.assertRaises(Hold):
                    asyncio.run(client.observe(STAGES[0]))
                self.assertTrue(client.held)

    def test_request_schema_rejected_before_collection(self):
        client, _ = self.pair()
        async def capture(raw):
            self.request = decode(raw)["message"]
            raise Hold("unit capture")
        client.exchange = capture
        with self.assertRaises(Hold):
            asyncio.run(client.observe(STAGES[0]))
        for change in ({"payload": {"unexpected": True}}, {"sample_seconds": 0.1},
                       {"stage": STAGES[1]}, {"seq": 2}):
            _, responder = self.pair()
            with self.subTest(change=change), self.assertRaises(Hold):
                asyncio.run(responder.respond(channel.signed(UNIT_KEY, self.request | change)))
        self.assertEqual(self.calls, [])

    def test_constructor_binding_types_and_no_key_in_messages_or_proof(self):
        client, _ = self.pair()
        result = asyncio.run(client.observe(STAGES[0]))
        self.assertFalse({"key", "_key", "secret_key"} & set(result["message_proof"]))
        self.assertNotIn(UNIT_KEY.hex(), json.dumps(result))
        self.assertNotIn(base64.b64encode(UNIT_KEY).decode(), json.dumps(result))
        self.assertTrue(all(UNIT_KEY not in raw for _, raw in self.records))
        for key in (b"short", "x" * 32, bytearray(32)):
            with self.assertRaises(Hold):
                channel.ObserverClient(lambda raw: raw, key, **self.binding, record=self.record)
        for update in ({"attempt": "../bad"}, {"binding": "a" * 63},
                       {"producer": "not a producer"}, {"role": "other"}):
            with self.assertRaises(Hold):
                channel.ObserverClient(lambda raw: raw, UNIT_KEY, **(self.binding | update), record=self.record)

    def test_actual_disposable_stdio_peer_handles_all_44_signed_exchanges(self):
        script = '''import asyncio, sys
sys.path.insert(0, sys.argv[1])
from observer_channel import ObserverResponder
from parent_contract import STAGES
async def provider(stage, nonce):
    return {"unit": "disposable-stdio-peer", "stage": stage}
server = ObserverResponder(provider, bytes(range(32)), attempt="S24-unit-attempt", binding="a"*64,
                           producer="UnitHost", role="host-memory", record=lambda direction, raw: None)
async def run():
    for _ in STAGES:
        raw = sys.stdin.buffer.readline(65537)
        reply = await server.respond(raw)
        sys.stdout.buffer.write(reply)
        sys.stdout.buffer.flush()
asyncio.run(run())
'''
        async def run():
            proc = await asyncio.create_subprocess_exec(sys.executable, "-I", "-B", "-c", script,
                str(Path(channel.__file__).parent), stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            try:
                async def exchange(raw):
                    proc.stdin.write(raw)
                    await proc.stdin.drain()
                    return await proc.stdout.readline()
                client = channel.ObserverClient(exchange, UNIT_KEY, **self.binding, record=self.record)
                for stage in STAGES:
                    result = await client.observe(stage)
                    self.assertEqual(result["payload"], {"unit": "disposable-stdio-peer", "stage": stage})
                proc.stdin.close()
                self.assertEqual(await asyncio.wait_for(proc.wait(), 3), 0)
                self.assertEqual(await proc.stderr.read(), b"")
            finally:
                proc.stdin.close()
                if proc.returncode is None:
                    proc.kill()  # Disposable unit child only, never a supplied PID/runtime.
                await proc.wait()
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
