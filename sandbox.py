#!/usr/bin/env python3
"""IPO Failure Short System — sandbox CLI (Version 0.1, paper trading only).

Daily workflow (no hindsight — enter data only as it becomes available):

  python sandbox.py init --start-date 2026-08-24
  python sandbox.py add-ipo TKR --company "Name" --ipo-date 2026-08-21 --ipo-price 20 \
      --range-low 20 --range-high 24 --revenue 55e6 --unprofitable \
      --market-cap 900e6 --secondary-pct 0.35
  python sandbox.py observe TKR --date 2026-08-24 --open 18.2 --high 18.6 \
      --low 17.1 --close 17.3 --volume 4200000
  python sandbox.py process-day --date 2026-08-24
  python sandbox.py score TKR
  python sandbox.py status
"""

import argparse
import json
import sys

from ipo_sandbox import config, engine
from ipo_sandbox.models import DailyBar, IPOCandidate
from ipo_sandbox.portfolio import compute_stats
from ipo_sandbox.report import write_daily_report
from ipo_sandbox.scoring import compute_score
from ipo_sandbox.store import SandboxState


def cmd_init(args):
    state = SandboxState.init(args.start_date)
    print(f"Sandbox initialized (v{config.STRATEGY_VERSION}, paper mode).")
    print(f"  Starting capital : ${config.STARTING_CAPITAL:.2f}")
    print(f"  Max gross short  : ${config.MAX_GROSS_EXPOSURE:.2f}")
    print(f"  Forward test     : {config.FORWARD_TEST_TRADING_DAYS} trading days from {args.start_date}")
    print(f"  State file       : {state.path}")


def cmd_add_ipo(args):
    state = SandboxState.load()
    ticker = args.ticker.upper()
    if ticker in state.candidates:
        print(f"{ticker} already tracked.", file=sys.stderr)
        sys.exit(1)
    profitable = None
    if args.profitable:
        profitable = True
    elif args.unprofitable:
        profitable = False
    state.candidates[ticker] = IPOCandidate(
        ticker=ticker,
        company=args.company,
        ipo_date=args.ipo_date,
        ipo_price=args.ipo_price,
        range_low=args.range_low,
        range_high=args.range_high,
        downsized=args.downsized,
        revenue=args.revenue,
        profitable=profitable,
        market_cap=args.market_cap,
        secondary_pct=args.secondary_pct,
        excluded=args.exclude,
        exclusion_reason=args.exclusion_reason or "",
        notes=args.notes or "",
    )
    state.save()
    print(f"Tracking {ticker} ({args.company}), IPO {args.ipo_date} at ${args.ipo_price:.2f}.")


def cmd_observe(args):
    state = SandboxState.load()
    ticker = args.ticker.upper()
    c = state.candidates.get(ticker)
    if c is None:
        print(f"Unknown ticker {ticker}. Run add-ipo first.", file=sys.stderr)
        sys.exit(1)
    if c.bar_for_date(args.date):
        print(f"{ticker} already has a bar for {args.date}.", file=sys.stderr)
        sys.exit(1)
    if c.bars and args.date <= c.bars[-1].date:
        print(f"Bars must be appended chronologically (last: {c.bars[-1].date}).", file=sys.stderr)
        sys.exit(1)
    c.bars.append(DailyBar(args.date, args.open, args.high, args.low, args.close, args.volume))
    state.save()
    s = compute_score(c)
    day_n = len(c.bars)
    print(f"{ticker} day-{day_n} bar recorded for {args.date}. "
          f"Score: {s['total']} | technical failure: {s['has_technical_failure']} | "
          f"qualifies: {s['qualifies']}")


def cmd_process_day(args):
    state = SandboxState.load()
    date = args.date
    if date in state.processed_days:
        print(f"{date} already processed.", file=sys.stderr)
        sys.exit(1)
    if state.processed_days and date <= state.processed_days[-1]:
        print(f"Days must be processed chronologically (last: {state.processed_days[-1]}).",
              file=sys.stderr)
        sys.exit(1)

    events = []

    # 1. Fill pending entries at today's open (qualified after a prior close).
    still_pending = []
    for pe in state.pending_entries:
        ticker = pe["ticker"]
        c = state.candidates.get(ticker)
        bar = c.bar_for_date(date) if c else None
        if bar is None:
            still_pending.append(pe)  # no bar today (halt/no data) — stays pending
            continue
        marks = state.latest_marks()
        open_count = len(state.open_positions())
        exposure = state.gross_exposure(marks)
        if open_count >= config.MAX_POSITIONS:
            events.append(f"SKIPPED entry {ticker}: max positions ({config.MAX_POSITIONS}) reached.")
            continue
        if exposure + config.POSITION_NOTIONAL > config.MAX_GROSS_EXPOSURE + 1e-6:
            events.append(f"SKIPPED entry {ticker}: gross exposure cap ${config.MAX_GROSS_EXPOSURE:.0f}.")
            continue
        pos = engine.open_position(ticker, pe["qualification_date"], date, bar.open)
        state.positions.append(pos)
        events.append(
            f"ENTERED short {ticker} at open {bar.open:.2f} "
            f"(effective {pos.entry_price_effective:.2f}, {pos.shares:.2f} sh, "
            f"stop {pos.stop_price:.2f}, T1 {pos.target1:.2f}, T2 {pos.target2:.2f})."
        )
        # Same-day management applies below via process_day.

    state.pending_entries = still_pending

    # 2. Manage open positions with today's bars.
    for pos in state.open_positions():
        c = state.candidates.get(pos.ticker)
        bar = c.bar_for_date(date) if c else None
        if bar is None:
            events.append(f"NO DATA for open position {pos.ticker} on {date} — no assumption made.")
            continue
        for fill in engine.process_day(pos, bar):
            events.append(
                f"{fill.reason.upper()} {pos.ticker}: covered {fill.fraction:.0%} at "
                f"{fill.raw_price:.2f} (effective {fill.effective_price:.2f}), "
                f"net ${fill.net_profit:.2f}."
            )

    # 3. After the close: check new qualifications -> entry at next open.
    pending_tickers = {pe["ticker"] for pe in state.pending_entries}
    for ticker, c in state.candidates.items():
        if state.has_position(ticker) or ticker in pending_tickers or c.excluded:
            continue
        if not c.bars:
            continue  # nothing observed yet
        s = compute_score(c)
        if s["qualifies"]:
            state.pending_entries.append({"ticker": ticker, "qualification_date": date})
            events.append(
                f"QUALIFIED {ticker} (score {s['total']}): synthetic short at next trading day's open."
            )

    # 4. Snapshot equity, count the forward-test day, write the report.
    state.processed_days.append(date)
    stats = compute_stats(state.positions, state.latest_marks(), state.equity_history)
    state.equity_history.append({"date": date, "equity": stats["current_equity"]})
    day_number = len(state.processed_days)

    if day_number >= state.meta.get("forward_test_trading_days", config.FORWARD_TEST_TRADING_DAYS) \
            and state.meta.get("status") == "active":
        state.meta["status"] = "test_complete"
        events.append("FORWARD TEST COMPLETE: evaluate results before creating Version 0.2.")

    notes = args.notes or ""
    if events:
        notes = (notes + " " if notes else "") + " ".join(events)
    else:
        notes = notes or "No qualifying IPOs and no position events today."

    state.meta["last_notes"] = notes
    path = write_daily_report(state, date, day_number, notes)
    state.save()

    print(f"Processed trading day {day_number}: {date}")
    for e in events:
        print(f"  - {e}")
    if not events:
        print("  - No events.")
    print(f"  Equity: ${stats['current_equity']:.2f}  |  Report: {path}")


def cmd_score(args):
    state = SandboxState.load()
    c = state.candidates.get(args.ticker.upper())
    if c is None:
        print(f"Unknown ticker {args.ticker}.", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(compute_score(c), indent=2))


def cmd_status(args):
    state = SandboxState.load()
    stats = compute_stats(state.positions, state.latest_marks(), state.equity_history)
    print(f"IPO Failure Short System v{config.STRATEGY_VERSION} — "
          f"{state.meta.get('environment')}/{state.meta.get('mode')} "
          f"({state.meta.get('status')})")
    print(f"Forward test: day {len(state.processed_days)} of "
          f"{state.meta.get('forward_test_trading_days')} "
          f"(started {state.meta.get('forward_test_start')})")
    print(f"Candidates tracked: {len(state.candidates)} | "
          f"Open positions: {len(state.open_positions())} | "
          f"Pending entries: {len(state.pending_entries)}")
    print(json.dumps(stats, indent=2))


def main(argv=None):
    p = argparse.ArgumentParser(description="IPO Failure Short System sandbox (paper only)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init", help="initialize sandbox state")
    sp.add_argument("--start-date", required=True)
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("add-ipo", help="track a new IPO candidate")
    sp.add_argument("ticker")
    sp.add_argument("--company", required=True)
    sp.add_argument("--ipo-date", required=True)
    sp.add_argument("--ipo-price", type=float, required=True)
    sp.add_argument("--range-low", type=float)
    sp.add_argument("--range-high", type=float)
    sp.add_argument("--downsized", action="store_true")
    sp.add_argument("--revenue", type=float)
    sp.add_argument("--market-cap", type=float)
    sp.add_argument("--secondary-pct", type=float)
    g = sp.add_mutually_exclusive_group()
    g.add_argument("--profitable", action="store_true")
    g.add_argument("--unprofitable", action="store_true")
    sp.add_argument("--exclude", action="store_true",
                    help="track but exclude (SPAC, direct listing, fund, etc.)")
    sp.add_argument("--exclusion-reason")
    sp.add_argument("--notes")
    sp.set_defaults(func=cmd_add_ipo)

    sp = sub.add_parser("observe", help="record a daily OHLCV bar for a candidate")
    sp.add_argument("ticker")
    sp.add_argument("--date", required=True)
    sp.add_argument("--open", type=float, required=True)
    sp.add_argument("--high", type=float, required=True)
    sp.add_argument("--low", type=float, required=True)
    sp.add_argument("--close", type=float, required=True)
    sp.add_argument("--volume", type=float, required=True)
    sp.set_defaults(func=cmd_observe)

    sp = sub.add_parser("process-day", help="run entries/exits/report for a trading day")
    sp.add_argument("--date", required=True)
    sp.add_argument("--notes")
    sp.set_defaults(func=cmd_process_day)

    sp = sub.add_parser("score", help="show a candidate's failure-score breakdown")
    sp.add_argument("ticker")
    sp.set_defaults(func=cmd_score)

    sp = sub.add_parser("status", help="show sandbox status and portfolio stats")
    sp.set_defaults(func=cmd_status)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
