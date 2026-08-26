"""Tests for the Alpaca paper client and mirror planner (no network)."""

import io
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ipo_sandbox import engine
from ipo_sandbox.alpaca import (
    PAPER_TRADING_URL, AlpacaError, AlpacaPaperClient, plan_mirror,
)
from ipo_sandbox.models import DailyBar

KEYS = {"APCA_API_KEY_ID": "test-key", "APCA_API_SECRET_KEY": "test-secret"}


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def fake_urlopen(responses):
    """responses: list of dicts to return, in call order. Records requests."""
    calls = []

    def _open(req, timeout=None):
        calls.append(req)
        return FakeResponse(json.dumps(responses[len(calls) - 1]).encode())

    _open.calls = calls
    return _open


class ClientSafetyTests(unittest.TestCase):
    def test_missing_keys_refused(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(AlpacaError):
                AlpacaPaperClient()

    def test_live_base_url_refused(self):
        env = dict(KEYS, APCA_API_BASE_URL="https://api.alpaca.markets")
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(AlpacaError) as ctx:
                AlpacaPaperClient()
            self.assertIn("paper endpoint", str(ctx.exception))

    def test_paper_base_url_accepted(self):
        env = dict(KEYS, APCA_API_BASE_URL=PAPER_TRADING_URL + "/")
        with mock.patch.dict(os.environ, env, clear=True):
            c = AlpacaPaperClient()
            self.assertEqual(c.trading_url, PAPER_TRADING_URL)

    def test_orders_are_whole_share(self):
        with mock.patch.dict(os.environ, KEYS, clear=True):
            c = AlpacaPaperClient()
            c._urlopen = fake_urlopen([{"id": "abc"}])
            c.submit_order("LYNX", 16.6, "sell")
            body = json.loads(c._urlopen.calls[0].data.decode())
            self.assertEqual(body["qty"], "16")
            self.assertEqual(body["side"], "sell")
            self.assertTrue(
                c._urlopen.calls[0].full_url.startswith(PAPER_TRADING_URL))

    def test_auth_headers_sent(self):
        with mock.patch.dict(os.environ, KEYS, clear=True):
            c = AlpacaPaperClient()
            c._urlopen = fake_urlopen([{"status": "ACTIVE"}])
            c.account()
            req = c._urlopen.calls[0]
            self.assertEqual(req.get_header("Apca-api-key-id"), "test-key")
            self.assertEqual(req.get_header("Apca-api-secret-key"), "test-secret")


class DataTests(unittest.TestCase):
    def test_daily_bars_parse_and_paginate(self):
        page1 = {"bars": [{"t": "2026-08-26T04:00:00Z", "o": 15.06, "h": 15.20,
                           "l": 13.50, "c": 13.94, "v": 1125199}],
                 "next_page_token": "tok"}
        page2 = {"bars": [{"t": "2026-08-27T04:00:00Z", "o": 13.90, "h": 14.00,
                           "l": 13.00, "c": 13.10, "v": 900000}],
                 "next_page_token": None}
        with mock.patch.dict(os.environ, KEYS, clear=True):
            c = AlpacaPaperClient()
            c._urlopen = fake_urlopen([page1, page2])
            bars = c.daily_bars("LYNX", "2026-08-26", "2026-08-27")
        self.assertEqual([b["date"] for b in bars], ["2026-08-26", "2026-08-27"])
        self.assertEqual(bars[0]["open"], 15.06)
        self.assertEqual(bars[1]["volume"], 900000.0)


class MirrorPlanTests(unittest.TestCase):
    def _sandbox_pos(self):
        pos = engine.open_position("LYNX", "2026-08-24", "2026-08-26", 15.06)
        return pos  # 16.60 shares short

    def test_open_short_to_match(self):
        intents = plan_mirror([self._sandbox_pos()], [])
        self.assertEqual(intents, [{"symbol": "LYNX", "side": "sell", "qty": 16,
                                    "reason": "open/extend short to match sandbox"}])

    def test_already_matched_is_noop(self):
        alpaca = [{"symbol": "LYNX", "qty": "-16", "side": "short"}]
        self.assertEqual(plan_mirror([self._sandbox_pos()], alpaca), [])

    def test_partial_cover_after_target1(self):
        pos = self._sandbox_pos()
        engine.process_day(pos, DailyBar("2026-08-27", 12.0, 12.5, 11.0, 11.4, 1e6))
        self.assertAlmostEqual(pos.remaining_fraction, 0.5)  # T1 covered half
        alpaca = [{"symbol": "LYNX", "qty": "-16", "side": "short"}]
        intents = plan_mirror([pos], alpaca)
        self.assertEqual(intents, [{"symbol": "LYNX", "side": "buy", "qty": 8,
                                    "reason": "cover to match sandbox"}])

    def test_closed_sandbox_position_covers_all(self):
        pos = self._sandbox_pos()
        engine.process_day(pos, DailyBar("2026-08-27", 16.0, 17.0, 15.5, 16.9, 1e6))
        self.assertFalse(pos.open)  # stopped out
        alpaca = [{"symbol": "LYNX", "qty": "-16", "side": "short"}]
        intents = plan_mirror([pos], alpaca)
        self.assertEqual(intents, [{"symbol": "LYNX", "side": "buy", "qty": 16,
                                    "reason": "cover to match sandbox"}])

    def test_stray_alpaca_position_closed(self):
        alpaca = [{"symbol": "GHOST", "qty": "-5", "side": "short"}]
        intents = plan_mirror([], alpaca)
        self.assertEqual(intents, [{"symbol": "GHOST", "side": "buy", "qty": 5,
                                    "reason": "close stray position not in sandbox"}])


if __name__ == "__main__":
    unittest.main()
