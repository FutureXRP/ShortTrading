"""Alpaca PAPER-trading client for integration testing (Phase 4 scaffold).

Hard safety rules:
- Keys come from environment variables APCA_API_KEY_ID / APCA_API_SECRET_KEY,
  never from files in this repo.
- The trading base URL is pinned to the paper endpoint. If APCA_API_BASE_URL
  is set to anything other than the paper endpoint, the client refuses to run.
  This module must never place a live order.

The sandbox engine remains the source of truth for decisions; Alpaca is the
execution/data layer used to measure how simulation differs from reality
(whole-share shorts, borrow availability, real fills).
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

PAPER_TRADING_URL = "https://paper-api.alpaca.markets"
DATA_URL = "https://data.alpaca.markets"


class AlpacaError(Exception):
    pass


class AlpacaPaperClient:
    def __init__(self, key_id=None, secret_key=None):
        self.key_id = key_id or os.environ.get("APCA_API_KEY_ID", "")
        self.secret_key = secret_key or os.environ.get("APCA_API_SECRET_KEY", "")
        if not self.key_id or not self.secret_key:
            raise AlpacaError(
                "Missing Alpaca keys. Export APCA_API_KEY_ID and "
                "APCA_API_SECRET_KEY (paper keys from the Alpaca dashboard)."
            )
        override = os.environ.get("APCA_API_BASE_URL", "").rstrip("/")
        if override and override != PAPER_TRADING_URL:
            raise AlpacaError(
                f"APCA_API_BASE_URL is set to {override!r}. This tool only "
                f"operates against the paper endpoint {PAPER_TRADING_URL} and "
                "will not run against anything else."
            )
        self.trading_url = PAPER_TRADING_URL
        self.data_url = DATA_URL
        self._urlopen = urllib.request.urlopen  # injectable for tests

    # ---------- plumbing ----------
    def _request(self, method, url, params=None, body=None):
        if params:
            url = url + "?" + urllib.parse.urlencode(params)
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "APCA-API-KEY-ID": self.key_id,
            "APCA-API-SECRET-KEY": self.secret_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        try:
            with self._urlopen(req, timeout=30) as resp:
                payload = resp.read().decode()
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:500]
            raise AlpacaError(f"HTTP {e.code} {method} {url}: {detail}") from e
        except urllib.error.URLError as e:
            raise AlpacaError(f"Network error reaching {url}: {e.reason}") from e
        return json.loads(payload) if payload else None

    def _trading(self, method, path, params=None, body=None):
        return self._request(method, f"{self.trading_url}/v2{path}", params, body)

    # ---------- trading API ----------
    def account(self):
        return self._trading("GET", "/account")

    def clock(self):
        return self._trading("GET", "/clock")

    def asset(self, symbol):
        return self._trading("GET", f"/assets/{symbol.upper()}")

    def positions(self):
        return self._trading("GET", "/positions") or []

    def position(self, symbol):
        try:
            return self._trading("GET", f"/positions/{symbol.upper()}")
        except AlpacaError as e:
            if "HTTP 404" in str(e):
                return None
            raise

    def open_orders(self):
        return self._trading("GET", "/orders", params={"status": "open", "limit": 500}) or []

    def submit_order(self, symbol, qty, side, order_type="market",
                     time_in_force="day", limit_price=None, stop_price=None):
        body = {
            "symbol": symbol.upper(),
            "qty": str(int(qty)),  # whole shares only — shorts can't be fractional
            "side": side,
            "type": order_type,
            "time_in_force": time_in_force,
        }
        if limit_price is not None:
            body["limit_price"] = f"{limit_price:.2f}"
        if stop_price is not None:
            body["stop_price"] = f"{stop_price:.2f}"
        return self._trading("POST", "/orders", body=body)

    def cancel_order(self, order_id):
        return self._trading("DELETE", f"/orders/{order_id}")

    # ---------- data API ----------
    def daily_bars(self, symbol, start, end, feed="iex"):
        """Daily OHLCV bars, [start, end] inclusive (YYYY-MM-DD), oldest first."""
        out = []
        page_token = None
        while True:
            params = {
                "timeframe": "1Day",
                "start": f"{start}T00:00:00Z",
                "end": f"{end}T23:59:59Z",
                "feed": feed,
                "adjustment": "raw",
                "limit": 1000,
            }
            if page_token:
                params["page_token"] = page_token
            resp = self._request(
                "GET", f"{self.data_url}/v2/stocks/{symbol.upper()}/bars", params)
            for b in resp.get("bars") or []:
                out.append({
                    "date": b["t"][:10],
                    "open": float(b["o"]),
                    "high": float(b["h"]),
                    "low": float(b["l"]),
                    "close": float(b["c"]),
                    "volume": float(b["v"]),
                })
            page_token = resp.get("next_page_token")
            if not page_token:
                return out


def plan_mirror(sandbox_positions, alpaca_positions):
    """Compute the orders needed to make the Alpaca paper book match the
    sandbox book. Pure function so it is unit-testable without a network.

    sandbox_positions: list[ipo_sandbox.models.Position]
    alpaca_positions: list of Alpaca position dicts ({"symbol", "qty", "side"}).
    Returns a list of intents: {"symbol", "side", "qty", "reason"}.
    Whole shares only; a sandbox remainder under 1 share rounds to 0.
    """
    alpaca_short_qty = {}
    for p in alpaca_positions:
        qty = abs(int(float(p["qty"])))
        if p.get("side") == "short" or float(p["qty"]) < 0:
            alpaca_short_qty[p["symbol"].upper()] = qty

    intents = []
    covered = set()
    for pos in sandbox_positions:
        symbol = pos.ticker.upper()
        covered.add(symbol)
        desired = int(pos.remaining_shares) if pos.open else 0
        have = alpaca_short_qty.get(symbol, 0)
        if desired > have:
            intents.append({"symbol": symbol, "side": "sell",
                            "qty": desired - have,
                            "reason": "open/extend short to match sandbox"})
        elif have > desired:
            intents.append({"symbol": symbol, "side": "buy",
                            "qty": have - desired,
                            "reason": "cover to match sandbox"})
    for symbol, have in alpaca_short_qty.items():
        if symbol not in covered and have > 0:
            intents.append({"symbol": symbol, "side": "buy", "qty": have,
                            "reason": "close stray position not in sandbox"})
    return intents
