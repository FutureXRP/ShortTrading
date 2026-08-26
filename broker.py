#!/usr/bin/env python3
"""Alpaca PAPER integration CLI — Phase 4 scaffold. Never places live orders.

Setup (on the machine where you run this — keys never go in the repo):

  export APCA_API_KEY_ID="...paper key id..."
  export APCA_API_SECRET_KEY="...paper secret..."

Commands:

  python3 broker.py check              verify keys, paper account, market clock
  python3 broker.py shortable TKR      borrow check: shortable / easy-to-borrow
  python3 broker.py sync-bars          pull daily OHLCV from Alpaca data API and
                                       feed missing bars into the sandbox
  python3 broker.py mirror [--execute] reconcile Alpaca paper book to the
                                       sandbox book (dry-run unless --execute)
  python3 broker.py status             Alpaca account, positions, open orders

The sandbox (sandbox.py) stays the decision engine and the record of truth.
Alpaca paper is the integration-test layer: real symbols, whole-share shorts,
real borrow checks, real rejections.
"""

import argparse
import sys
from datetime import date, timedelta

from ipo_sandbox.alpaca import AlpacaError, AlpacaPaperClient, plan_mirror
from ipo_sandbox.models import DailyBar
from ipo_sandbox.store import SandboxState

BANNER = "[PAPER] Alpaca paper endpoint only — no live trading possible from this tool."


def client_or_exit():
    try:
        return AlpacaPaperClient()
    except AlpacaError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_check(args):
    print(BANNER)
    c = client_or_exit()
    acct = c.account()
    clock = c.clock()
    print(f"Account   : {acct.get('account_number')} ({acct.get('status')})")
    print(f"Equity    : ${float(acct.get('equity', 0)):,.2f} paper")
    print(f"Shorting  : {'enabled' if acct.get('shorting_enabled') else 'DISABLED'}")
    print(f"Market    : {'OPEN' if clock.get('is_open') else 'closed'} "
          f"(next open {clock.get('next_open')}, next close {clock.get('next_close')})")
    print("Connection OK.")


def cmd_shortable(args):
    print(BANNER)
    c = client_or_exit()
    a = c.asset(args.ticker)
    print(f"{a.get('symbol')} ({a.get('exchange')}) — {a.get('name')}")
    print(f"  tradable      : {a.get('tradable')}")
    print(f"  shortable     : {a.get('shortable')}")
    print(f"  easy_to_borrow: {a.get('easy_to_borrow')}")
    if not a.get("shortable"):
        print("  NOTE: not shortable on Alpaca right now — in live trading this "
              "trade could not be taken. Record this in the trial journal.")


def cmd_sync_bars(args):
    print(BANNER)
    c = client_or_exit()
    state = SandboxState.load()
    end = args.date or date.today().isoformat()
    added = 0
    for ticker, cand in sorted(state.candidates.items()):
        if cand.excluded and not state.has_position(ticker):
            continue
        start = cand.bars[-1].date if cand.bars else cand.ipo_date
        start = (date.fromisoformat(start)).isoformat()
        try:
            bars = c.daily_bars(ticker, start, end)
        except AlpacaError as e:
            print(f"{ticker}: fetch failed — {e}")
            continue
        for b in bars:
            if cand.bar_for_date(b["date"]) or (cand.bars and b["date"] <= cand.bars[-1].date):
                continue
            cand.bars.append(DailyBar(b["date"], b["open"], b["high"],
                                      b["low"], b["close"], b["volume"]))
            added += 1
            print(f"{ticker}: added {b['date']} "
                  f"O {b['open']:.2f} H {b['high']:.2f} L {b['low']:.2f} "
                  f"C {b['close']:.2f} V {b['volume']:,.0f}")
    state.save()
    print(f"{added} bar(s) added. Next: python3 sandbox.py process-day --date <DATE> "
          "for each new trading day, oldest first.")


def cmd_mirror(args):
    print(BANNER)
    c = client_or_exit()
    state = SandboxState.load()
    intents = plan_mirror(state.positions, c.positions())
    if not intents:
        print("Alpaca paper book already matches the sandbox book.")
        return
    for it in intents:
        line = f"{it['side'].upper():4} {it['qty']} {it['symbol']} — {it['reason']}"
        if not args.execute:
            print(f"DRY-RUN: {line}")
            continue
        try:
            order = c.submit_order(it["symbol"], it["qty"], it["side"])
            print(f"SUBMITTED: {line} (order {order.get('id', '?')[:8]})")
        except AlpacaError as e:
            print(f"REJECTED : {line}\n  {e}")
            print("  A short rejection usually means no borrow — that is real "
                  "integration data; record it in the trial journal.")
    if not args.execute:
        print("Re-run with --execute to submit these paper orders.")


def cmd_status(args):
    print(BANNER)
    c = client_or_exit()
    acct = c.account()
    print(f"Paper equity ${float(acct.get('equity', 0)):,.2f} | "
          f"cash ${float(acct.get('cash', 0)):,.2f}")
    positions = c.positions()
    if not positions:
        print("No open Alpaca positions.")
    for p in positions:
        print(f"  {p['symbol']:6} {p['side']:5} {p['qty']:>6} sh "
              f"@ avg {float(p['avg_entry_price']):.2f} | "
              f"mark {float(p['current_price']):.2f} | "
              f"unrealized ${float(p['unrealized_pl']):.2f}")
    orders = c.open_orders()
    if orders:
        print("Open orders:")
        for o in orders:
            print(f"  {o['symbol']:6} {o['side']:5} {o['qty']:>6} {o['type']} "
                  f"{o.get('stop_price') or o.get('limit_price') or ''} ({o['status']})")


def main(argv=None):
    p = argparse.ArgumentParser(description="Alpaca paper integration (Phase 4 scaffold)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="verify keys, account, market clock").set_defaults(func=cmd_check)
    sp = sub.add_parser("shortable", help="borrow availability for a ticker")
    sp.add_argument("ticker")
    sp.set_defaults(func=cmd_shortable)
    sp = sub.add_parser("sync-bars", help="pull daily bars into the sandbox")
    sp.add_argument("--date", help="end date YYYY-MM-DD (default today)")
    sp.set_defaults(func=cmd_sync_bars)
    sp = sub.add_parser("mirror", help="reconcile Alpaca paper book to sandbox book")
    sp.add_argument("--execute", action="store_true",
                    help="actually submit paper orders (default: dry run)")
    sp.set_defaults(func=cmd_mirror)
    sub.add_parser("status", help="Alpaca account, positions, open orders").set_defaults(func=cmd_status)
    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
