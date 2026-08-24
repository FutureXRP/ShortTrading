"""JSON persistence for sandbox state (sandbox_data/state.json)."""

import json
import os

from . import config
from .models import IPOCandidate, Position

DEFAULT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sandbox_data")


class SandboxState:
    def __init__(self, data_dir: str = DEFAULT_DIR):
        self.data_dir = data_dir
        self.path = os.path.join(data_dir, "state.json")
        self.meta = {}
        self.candidates = {}   # ticker -> IPOCandidate
        self.positions = []    # list[Position], open and closed
        self.equity_history = []  # [{"date", "equity"}]
        self.processed_days = []  # trading dates already processed
        self.pending_entries = []  # [{"ticker", "qualification_date"}] awaiting next open

    # ---------- persistence ----------
    def save(self):
        os.makedirs(self.data_dir, exist_ok=True)
        payload = {
            "meta": self.meta,
            "candidates": {t: c.to_dict() for t, c in self.candidates.items()},
            "positions": [p.to_dict() for p in self.positions],
            "equity_history": self.equity_history,
            "processed_days": self.processed_days,
            "pending_entries": self.pending_entries,
        }
        with open(self.path, "w") as f:
            json.dump(payload, f, indent=2)

    @classmethod
    def load(cls, data_dir: str = DEFAULT_DIR) -> "SandboxState":
        state = cls(data_dir)
        if not os.path.exists(state.path):
            raise FileNotFoundError(
                f"No sandbox state at {state.path}. Run `python sandbox.py init` first."
            )
        with open(state.path) as f:
            payload = json.load(f)
        state.meta = payload.get("meta", {})
        state.candidates = {
            t: IPOCandidate.from_dict(c) for t, c in payload.get("candidates", {}).items()
        }
        state.positions = [Position.from_dict(p) for p in payload.get("positions", [])]
        state.equity_history = payload.get("equity_history", [])
        state.processed_days = payload.get("processed_days", [])
        state.pending_entries = payload.get("pending_entries", [])
        return state

    @classmethod
    def init(cls, start_date: str, data_dir: str = DEFAULT_DIR) -> "SandboxState":
        state = cls(data_dir)
        state.meta = {
            "system": "IPO Failure Short System",
            "strategy_version": config.STRATEGY_VERSION,
            "environment": "sandbox",
            "mode": "paper",
            "live_capital": 0.0,
            "starting_capital": config.STARTING_CAPITAL,
            "max_gross_exposure": config.MAX_GROSS_EXPOSURE,
            "forward_test_start": start_date,
            "forward_test_trading_days": config.FORWARD_TEST_TRADING_DAYS,
            "status": "active",
        }
        state.save()
        return state

    # ---------- helpers ----------
    def open_positions(self):
        return [p for p in self.positions if p.open]

    def gross_exposure(self, marks: dict) -> float:
        total = 0.0
        for p in self.open_positions():
            mark = marks.get(p.ticker, p.entry_price_raw)
            total += mark * p.remaining_shares
        return total

    def has_position(self, ticker: str) -> bool:
        return any(p.ticker == ticker for p in self.positions)

    def latest_marks(self) -> dict:
        marks = {}
        for p in self.open_positions():
            c = self.candidates.get(p.ticker)
            if c and c.bars:
                marks[p.ticker] = c.bars[-1].close
            else:
                marks[p.ticker] = p.entry_price_raw
        return marks
