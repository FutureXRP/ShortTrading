"""Daily sandbox report generator (build.md section 35)."""

import os

from . import config
from .portfolio import compute_stats
from .scoring import compute_score


def _fmt(v, money=False):
    if v is None:
        return "—"
    if money:
        return f"${v:,.2f}"
    return str(v)


def build_daily_report(state, date: str, day_number: int, notes: str = "") -> str:
    lines = []
    lines.append(f"# Daily Sandbox Report — {date}")
    lines.append("")
    lines.append(f"**System:** IPO Failure Short System v{config.STRATEGY_VERSION} (paper / sandbox)")
    lines.append(f"**Forward-test trading day:** {day_number} of {state.meta.get('forward_test_trading_days')}")
    lines.append("")

    if notes:
        lines.append(f"> {notes}")
        lines.append("")

    # --- IPO screening ---
    lines.append("## IPO Screening")
    lines.append("")
    if not state.candidates:
        lines.append("_No IPO candidates tracked yet._")
    else:
        lines.append("| Ticker | Company | IPO date | IPO px | D1 close | D1 low | D2 close | Score | Technical? | Qualifies? |")
        lines.append("|---|---|---|---:|---:|---:|---:|---:|---|---|")
        for t, c in sorted(state.candidates.items()):
            s = compute_score(c)
            d1 = c.bar_for_day(1)
            d2 = c.bar_for_day(2)
            status = "EXCLUDED" if c.excluded else ("YES" if s["qualifies"] else "no")
            row = [
                t,
                c.company,
                c.ipo_date,
                f"{c.ipo_price:.2f}",
                f"{d1.close:.2f}" if d1 else "—",
                f"{d1.low:.2f}" if d1 else "—",
                f"{d2.close:.2f}" if d2 else "—",
                str(s["total"]),
                "yes" if s["has_technical_failure"] else "no",
                status,
            ]
            lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    # --- Positions ---
    lines.append("## Positions")
    lines.append("")
    open_positions = state.open_positions()
    closed = [p for p in state.positions if not p.open]
    if not state.positions:
        lines.append("_No positions entered yet._")
    else:
        lines.append("| Ticker | Entry date | Entry px | Shares | Stop | T1 | T2 | Remaining | Days held | Realized | Status |")
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|")
        marks = state.latest_marks()
        for p in state.positions:
            status = "OPEN" if p.open else "CLOSED"
            lines.append(
                "| " + " | ".join([
                    p.ticker,
                    p.entry_date,
                    f"{p.entry_price_raw:.2f}",
                    f"{p.shares:.2f}",
                    f"{p.stop_price:.2f}",
                    f"{p.target1:.2f}",
                    f"{p.target2:.2f}",
                    f"{p.remaining_fraction:.0%}",
                    str(p.trading_days_held),
                    f"${p.realized_net():.2f}",
                    status,
                ]) + " |"
            )
        if open_positions:
            lines.append("")
            for p in open_positions:
                mark = marks.get(p.ticker, p.entry_price_raw)
                lines.append(
                    f"- **{p.ticker}** marked at {mark:.2f}: unrealized "
                    f"${p.unrealized_net(mark):.2f}"
                )
    if state.pending_entries:
        lines.append("")
        for pe in state.pending_entries:
            lines.append(
                f"- **Pending entry:** {pe['ticker']} qualified {pe['qualification_date']}; "
                f"short at next trading day's open."
            )
    lines.append("")

    # --- Portfolio statistics ---
    lines.append("## Portfolio Statistics")
    lines.append("")
    stats = compute_stats(state.positions, state.latest_marks(), state.equity_history)
    for key, label, money in [
        ("starting_equity", "Starting equity", True),
        ("current_equity", "Current equity", True),
        ("realized_pnl", "Realized P/L", True),
        ("unrealized_pnl", "Unrealized P/L", True),
        ("gross_exposure", "Gross short exposure", True),
        ("num_trades", "Closed trades", False),
        ("winning_trades", "Winners", False),
        ("losing_trades", "Losers", False),
        ("win_rate", "Win rate", False),
        ("expectancy_per_trade", "Expectancy / trade", True),
        ("profit_factor", "Profit factor", False),
        ("max_drawdown_pct", "Max drawdown %", False),
        ("return_on_initial_capital_pct", "Return on initial capital %", False),
    ]:
        lines.append(f"- **{label}:** {_fmt(stats[key], money)}")
    lines.append("")
    return "\n".join(lines)


def write_daily_report(state, date: str, day_number: int, notes: str = "",
                       reports_dir: str = None) -> str:
    if reports_dir is None:
        reports_dir = os.path.join(os.path.dirname(state.data_dir), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    content = build_daily_report(state, date, day_number, notes)
    path = os.path.join(reports_dir, f"{date}.md")
    with open(path, "w") as f:
        f.write(content + "\n")
    return path
