"""Data models for the sandbox. All state is plain-dict serializable (JSON store)."""

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class DailyBar:
    date: str  # YYYY-MM-DD
    open: float
    high: float
    low: float
    close: float
    volume: float

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


@dataclass
class IPOCandidate:
    ticker: str
    company: str
    ipo_date: str          # YYYY-MM-DD (first trading day)
    ipo_price: float
    range_low: Optional[float] = None
    range_high: Optional[float] = None
    downsized: bool = False
    revenue: Optional[float] = None        # latest annual / TTM revenue, USD
    profitable: Optional[bool] = None      # latest FY / TTM net income positive?
    market_cap: Optional[float] = None     # approximate IPO market cap, USD
    secondary_pct: Optional[float] = None  # fraction of offered shares sold by insiders (0-1)
    excluded: bool = False
    exclusion_reason: str = ""
    notes: str = ""
    bars: list = field(default_factory=list)  # list[DailyBar], chronological

    def bar_for_day(self, n: int) -> Optional[DailyBar]:
        """1-indexed trading day since IPO (day 1 = IPO day)."""
        if 1 <= n <= len(self.bars):
            return self.bars[n - 1]
        return None

    def bar_for_date(self, date: str) -> Optional[DailyBar]:
        for b in self.bars:
            if b.date == date:
                return b
        return None

    def to_dict(self):
        d = asdict(self)
        d["bars"] = [b.to_dict() if isinstance(b, DailyBar) else b for b in self.bars]
        return d

    @classmethod
    def from_dict(cls, d):
        d = dict(d)
        d["bars"] = [DailyBar.from_dict(b) for b in d.get("bars", [])]
        return cls(**d)


@dataclass
class TradeFill:
    """One realized cover (partial or full)."""
    date: str
    fraction: float          # fraction of original position covered
    shares: float
    raw_price: float         # trigger/reference price before slippage
    effective_price: float   # buy-to-cover price after slippage
    reason: str              # stop | target1 | target2 | time_stop | test_end
    gross_profit: float
    borrow_cost: float
    slippage_cost: float
    net_profit: float

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


@dataclass
class Position:
    ticker: str
    qualification_date: str
    entry_date: str
    entry_price_raw: float       # next-day open used for levels
    entry_price_effective: float # short-sale proceeds price after slippage
    shares: float                # original share count (synthetic, fractional ok)
    notional: float
    stop_price: float
    target1: float
    target2: float
    remaining_fraction: float = 1.0
    stop_moved_to_entry: bool = False
    trading_days_held: int = 0
    open: bool = True
    fills: list = field(default_factory=list)  # list[TradeFill]
    max_favorable_price: Optional[float] = None  # lowest low seen
    max_adverse_price: Optional[float] = None    # highest high seen

    def to_dict(self):
        d = asdict(self)
        d["fills"] = [f.to_dict() if isinstance(f, TradeFill) else f for f in self.fills]
        return d

    @classmethod
    def from_dict(cls, d):
        d = dict(d)
        d["fills"] = [TradeFill.from_dict(f) for f in d.get("fills", [])]
        return cls(**d)

    @property
    def remaining_shares(self) -> float:
        return self.shares * self.remaining_fraction

    def realized_net(self) -> float:
        return sum(f.net_profit for f in self.fills)

    def unrealized_net(self, mark_price: float) -> float:
        if not self.open or self.remaining_fraction <= 0:
            return 0.0
        return (self.entry_price_effective - mark_price) * self.remaining_shares
