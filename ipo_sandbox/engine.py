"""Trade engine: entries, stops, targets, time stop, slippage, borrow cost.

Conservative intraday assumption (build.md section 32): when a stop and a
target could both have been hit in the same session and ordering cannot be
established from daily OHLC, assume the stop occurred first. We apply this
consistently: the stop in force at the start of the day is checked before any
target, and after Target #1 fills intraday the moved-to-entry stop is checked
before Target #2.
"""

from datetime import date as _date
from typing import Optional

from . import config
from .models import DailyBar, Position, TradeFill


def _days_between(d1: str, d2: str) -> int:
    return (_date.fromisoformat(d2) - _date.fromisoformat(d1)).days


def open_position(ticker: str, qualification_date: str, entry_date: str,
                  entry_open: float, notional: float = config.POSITION_NOTIONAL) -> Position:
    """Enter a synthetic short at the entry day's open, penalized by slippage.

    Levels (stop/targets) are set from the raw open; short-sale proceeds are
    booked at open * (1 - slippage), i.e. we sell lower than the print.
    """
    effective = entry_open * (1.0 - config.SLIPPAGE_PCT)
    shares = notional / entry_open
    return Position(
        ticker=ticker,
        qualification_date=qualification_date,
        entry_date=entry_date,
        entry_price_raw=entry_open,
        entry_price_effective=effective,
        shares=shares,
        notional=notional,
        stop_price=entry_open * (1.0 + config.STOP_PCT),
        target1=entry_open * (1.0 - config.TARGET1_PCT),
        target2=entry_open * (1.0 - config.TARGET2_PCT),
        max_favorable_price=entry_open,
        max_adverse_price=entry_open,
    )


def _cover(pos: Position, date: str, fraction_of_original: float,
           raw_price: float, reason: str) -> TradeFill:
    """Buy to cover a fraction of the original position, slippage against us."""
    effective = raw_price * (1.0 + config.SLIPPAGE_PCT)
    shares = pos.shares * fraction_of_original
    gross = (pos.entry_price_effective - raw_price) * shares
    slippage_cost = (effective - raw_price) * shares
    borrow_days = max(_days_between(pos.entry_date, date), 1)
    borrow_cost = (pos.entry_price_effective * shares) * config.BORROW_RATE_ANNUAL * borrow_days / 365.0
    net = (pos.entry_price_effective - effective) * shares - borrow_cost
    fill = TradeFill(
        date=date,
        fraction=fraction_of_original,
        shares=shares,
        raw_price=raw_price,
        effective_price=effective,
        reason=reason,
        gross_profit=gross,
        borrow_cost=borrow_cost,
        slippage_cost=slippage_cost,
        net_profit=net,
    )
    pos.fills.append(fill)
    pos.remaining_fraction = round(pos.remaining_fraction - fraction_of_original, 10)
    if pos.remaining_fraction <= 1e-9:
        pos.remaining_fraction = 0.0
        pos.open = False
    return fill


def process_day(pos: Position, bar: DailyBar) -> list:
    """Advance an open position through one trading day of OHLC.

    Returns the list of fills executed during the day.
    Entry day itself is also processed (stops/targets active from entry).
    """
    if not pos.open:
        return []

    fills = []
    pos.trading_days_held += 1
    pos.max_favorable_price = min(pos.max_favorable_price or bar.low, bar.low)
    pos.max_adverse_price = max(pos.max_adverse_price or bar.high, bar.high)

    # 1. Stop in force at start of day — checked first (conservative).
    if bar.high >= pos.stop_price:
        # If the open gapped through the stop, we fill at the open (worse).
        fill_price = max(bar.open, pos.stop_price)
        fills.append(_cover(pos, bar.date, pos.remaining_fraction, fill_price, "stop"))
        return fills

    # 2. Target #1 (only while full position is on).
    if pos.remaining_fraction >= 1.0 - 1e-9 and bar.low <= pos.target1:
        fill_price = min(bar.open, pos.target1)  # gap below target fills better
        fills.append(_cover(pos, bar.date, config.TARGET1_COVER_FRACTION, fill_price, "target1"))
        # Stop moves to entry for the remainder (section 26).
        pos.stop_price = pos.entry_price_raw
        pos.stop_moved_to_entry = True
        # Conservative: if the day also traded at/above the new stop, assume
        # the remainder was stopped at entry before any further downside.
        if bar.high >= pos.stop_price:
            fills.append(_cover(pos, bar.date, pos.remaining_fraction, pos.stop_price, "stop"))
            return fills

    # 3. Target #2 covers the remainder.
    if pos.open and pos.remaining_fraction > 0 and pos.remaining_fraction < 1.0 and bar.low <= pos.target2:
        fill_price = min(bar.open, pos.target2)
        fills.append(_cover(pos, bar.date, pos.remaining_fraction, fill_price, "target2"))
        return fills

    # 4. Time stop after 20 trading days (section 28) — close at the day's close.
    if pos.open and pos.trading_days_held >= config.TIME_STOP_TRADING_DAYS:
        fills.append(_cover(pos, bar.date, pos.remaining_fraction, bar.close, "time_stop"))

    return fills


def close_at_price(pos: Position, date: str, price: float, reason: str) -> Optional[TradeFill]:
    """Force-close the remainder (e.g. end of forward test)."""
    if not pos.open or pos.remaining_fraction <= 0:
        return None
    return _cover(pos, date, pos.remaining_fraction, price, reason)
