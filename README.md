# IPO Failure Short System — Sandbox App (v0.1)

Paper-trading implementation of the strategy specified in [build.md](build.md).
**No real money, no broker connection — sandbox mode only** (`meta.mode = "paper"`, live capital $0).

## Layout

```
build.md            strategy specification (Version 0.1)
sandbox.py          CLI entry point
ipo_sandbox/        engine package (stdlib only, Python 3.11+)
  config.py         v0.1 rule constants (capital, scores, stops, targets, costs)
  models.py         IPOCandidate / DailyBar / Position / TradeFill
  scoring.py        IPO Failure Score + qualification (sections 9-18)
  engine.py         entries, stops, targets, time stop, slippage, borrow (19-32)
  portfolio.py      equity, expectancy, profit factor, drawdown (36-39)
  store.py          JSON state persistence
  report.py         daily sandbox report generator (35)
sandbox_data/       state.json — the forward test's single source of truth
reports/            one markdown report per processed trading day
tests/              unit tests (python3 -m unittest discover -s tests)
```

## Daily forward-test workflow (no hindsight)

Each U.S. trading day, after the close:

```bash
# 1. Track any new operating-company IPOs (SPACs/direct listings: --exclude)
python3 sandbox.py add-ipo TKR --company "Name" --ipo-date YYYY-MM-DD --ipo-price 20 \
    --range-low 20 --range-high 24 --unprofitable --revenue 55e6 \
    --market-cap 900e6 --secondary-pct 0.35

# 2. Record today's OHLCV for every tracked candidate / open position
python3 sandbox.py observe TKR --date YYYY-MM-DD --open 18.2 --high 18.6 \
    --low 17.1 --close 17.3 --volume 4200000

# 3. Process the day: fills pending entries at today's open, applies
#    stops/targets/time stop to open positions, checks new qualifications,
#    snapshots equity, writes reports/YYYY-MM-DD.md
python3 sandbox.py process-day --date YYYY-MM-DD

# Inspection
python3 sandbox.py score TKR
python3 sandbox.py status

# 4. Refresh the dashboard page
python3 dashboard.py          # regenerates dashboard.html from state.json
```

## Alpaca paper integration (Phase 4 scaffold)

`broker.py` wires the sandbox to Alpaca's **paper** trading API for integration
testing. It is hard-pinned to the paper endpoint — it refuses to run against a
live URL, and orders are whole-share only. Setup (keys never go in the repo):

```bash
export APCA_API_KEY_ID="...paper key id..."
export APCA_API_SECRET_KEY="...paper secret..."

python3 broker.py check            # verify keys, paper account, market clock
python3 broker.py shortable LYNX   # borrow check (build.md section 31)
python3 broker.py sync-bars        # pull daily OHLCV into the sandbox
python3 broker.py mirror           # dry-run reconcile paper book to sandbox book
python3 broker.py mirror --execute # submit the paper orders
python3 broker.py status           # Alpaca account, positions, open orders
```

Daily flow with Alpaca connected: `sync-bars` → `sandbox.py process-day` for
each new date (oldest first) → `mirror --execute` → `dashboard.py`. The sandbox
stays the decision engine and record of truth; Alpaca paper measures execution
reality (borrow rejections, whole-share rounding, real fills vs. the 0.5%
slippage model).

## Viewing the trial

- **Dashboard**: `python3 dashboard.py` renders `dashboard.html` — open it in any
  browser (it is also published as a Claude artifact page after each processed day).
- **Daily reports**: one markdown file per trading day in `reports/`.
- **Terminal**: `python3 sandbox.py status` prints live portfolio statistics.

Rules enforced by the engine (from build.md): score ≥5 **and** a technical
failure signal to qualify (fading volume alone never qualifies); entry at the
next observed open; $250 notional per position, max 4 positions / $1,000 gross;
stop 10% above entry; cover half at −25% and move the stop to entry; cover the
rest at −50%; 20-trading-day time stop; 0.5% slippage against every fill; 30%
annualized borrow prorated by calendar days; when a stop and target were both
touchable in one session, the stop is assumed to have hit first — including the
moved-to-entry stop after a same-day Target #1 fill.

Unknown fundamental/offering data scores **zero** points (missing data biases
against taking a trade, never toward it).

## Forward test status

Started **2026-08-24** (10 trading days, Version 0.1). State and daily reports
are committed to the repo so the trial record is append-only and auditable.
