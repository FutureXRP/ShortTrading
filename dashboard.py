#!/usr/bin/env python3
"""Render the sandbox trial state to a self-contained HTML dashboard.

Usage: python3 dashboard.py [output.html]
Reads sandbox_data/state.json; writes dashboard.html by default.
The file is a body fragment (title + styles + content) so it renders both as a
local file and as a published artifact page.
"""

import html
import sys

from ipo_sandbox import config
from ipo_sandbox.portfolio import compute_stats
from ipo_sandbox.scoring import compute_score
from ipo_sandbox.store import SandboxState

SIGNAL_LABELS = [
    ("unprofitable", "Unprofitable (latest FY / TTM)", 2),
    ("revenue_below_100m", "Revenue below $100M", 1),
    ("valuation_above_10x", "IPO valuation above 10× sales", 1),
    ("weak_offering", "Priced below range or downsized", 1),
    ("secondary_above_30pct", "Secondary shares above 30%", 1),
    ("day1_close_below_ipo", "Day-1 close below IPO price", 2),
    ("day2_close_below_day1_low", "Day-2 close below Day-1 low", 2),
    ("day2_volume_below_day1", "Day-2 volume below Day-1", 1),
]


def esc(v):
    return html.escape(str(v))


def money(v, sign=False):
    if v is None:
        return "—"
    s = f"{abs(v):,.2f}"
    if sign and v > 0:
        return f"+${s}"
    if v < 0:
        return f"−${s}"
    return f"${s}"


def render(state) -> str:
    stats = compute_stats(state.positions, state.latest_marks(), state.equity_history)
    day_n = len(state.processed_days)
    total_days = state.meta.get("forward_test_trading_days", config.FORWARD_TEST_TRADING_DAYS)
    last_day = state.processed_days[-1] if state.processed_days else "—"
    status = state.meta.get("status", "active")
    pending = {pe["ticker"]: pe for pe in state.pending_entries}

    # ---- screening rows ----
    rows = []
    for t, c in sorted(state.candidates.items()):
        s = compute_score(c)
        d1 = c.bar_for_day(1)
        pos = next((p for p in state.positions if p.ticker == t), None)
        if c.excluded:
            pill = f'<span class="pill pill-mut">Excluded</span>'
            detail = esc(c.exclusion_reason)
        elif pos and pos.open:
            pill = '<span class="pill pill-short">Short open</span>'
            detail = f"entered {esc(pos.entry_date)}"
        elif pos:
            pill = '<span class="pill pill-mut">Closed</span>'
            detail = f"net {money(pos.realized_net(), sign=True)}"
        elif t in pending:
            pill = '<span class="pill pill-amber">Entry pending</span>'
            detail = "short at next open"
        elif s["qualifies"]:
            pill = '<span class="pill pill-good">Qualified</span>'
            detail = ""
        else:
            pill = '<span class="pill pill-mut">Watching</span>'
            detail = ""
        rows.append(
            "<tr>"
            f'<td class="mono strong">{esc(t)}</td>'
            f"<td>{esc(c.company)}<div class='sub'>{detail}</div></td>"
            f'<td class="mono">{esc(c.ipo_date)}</td>'
            f'<td class="mono num">{money(c.ipo_price) if c.ipo_price else "—"}</td>'
            f'<td class="mono num">{money(d1.close) if d1 else "—"}</td>'
            f'<td class="mono num strong">{s["total"] if not c.excluded else "—"}</td>'
            f"<td>{pill}</td>"
            "</tr>"
        )
    screening = "\n".join(rows) or '<tr><td colspan="7" class="sub">No candidates tracked yet.</td></tr>'

    # ---- score breakdowns for interesting candidates ----
    breakdowns = []
    for t, c in sorted(state.candidates.items()):
        if c.excluded:
            continue
        s = compute_score(c)
        items = []
        for key, label, pts in SIGNAL_LABELS:
            got = s["signals"][key]
            cls = "hit" if got else "miss"
            items.append(
                f'<li class="{cls}"><span>{esc(label)}</span>'
                f'<span class="mono">{"+" + str(got) if got else "0"}/{pts}</span></li>'
            )
        verdict = "QUALIFIES" if s["qualifies"] else "does not qualify"
        breakdowns.append(
            f'<div class="scorecard"><div class="scorehead">'
            f'<span class="mono strong">{esc(t)}</span>'
            f'<span class="mono">score {s["total"]} / 11 · {verdict}</span></div>'
            f'<ul class="signals">{"".join(items)}</ul></div>'
        )
    breakdown_html = "".join(breakdowns) or '<p class="sub">No scored candidates yet.</p>'

    # ---- order tickets ----
    tickets = []
    for pe in state.pending_entries:
        tickets.append(
            f'<div class="ticket"><div class="tickethead">'
            f'<span class="mono strong">{esc(pe["ticker"])}</span>'
            f'<span class="pill pill-amber">Pending</span></div>'
            f'<p>Qualified {esc(pe["qualification_date"])}. Synthetic short '
            f'{money(config.POSITION_NOTIONAL)} fills at the next observed open; '
            f"levels set from that open: stop +{config.STOP_PCT:.0%}, "
            f"T1 −{config.TARGET1_PCT:.0%} (cover half, stop to entry), "
            f"T2 −{config.TARGET2_PCT:.0%}, time stop "
            f"{config.TIME_STOP_TRADING_DAYS} trading days.</p></div>"
        )
    for p in state.positions:
        state_pill = ('<span class="pill pill-short">Open</span>' if p.open
                      else '<span class="pill pill-mut">Closed</span>')
        mark = state.latest_marks().get(p.ticker, p.entry_price_raw)
        line = (f"Unrealized {money(p.unrealized_net(mark), sign=True)} at mark {money(mark)}"
                if p.open else f"Net realized {money(p.realized_net(), sign=True)}")
        tickets.append(
            f'<div class="ticket"><div class="tickethead">'
            f'<span class="mono strong">{esc(p.ticker)}</span>{state_pill}</div>'
            f'<div class="grid2 mono">'
            f"<span>Entry {esc(p.entry_date)}</span><span class='num'>{money(p.entry_price_raw)}</span>"
            f"<span>Stop</span><span class='num'>{money(p.stop_price)}</span>"
            f"<span>Target 1 / 2</span><span class='num'>{money(p.target1)} / {money(p.target2)}</span>"
            f"<span>Remaining</span><span class='num'>{p.remaining_fraction:.0%}</span>"
            f"</div><p>{line}</p></div>"
        )
    tickets_html = "".join(tickets) or '<p class="sub">No positions and no pending entries.</p>'

    # ---- 10-day tracker ----
    cells = []
    for i in range(total_days):
        if i < day_n:
            eq = state.equity_history[i]["equity"] if i < len(state.equity_history) else None
            cells.append(
                f'<div class="daycell done" title="{esc(state.processed_days[i])}">'
                f'<span>D{i+1}</span><span class="mono">{money(eq)}</span></div>'
            )
        else:
            cells.append(f'<div class="daycell"><span>D{i+1}</span><span class="mono">·</span></div>')
    tracker = "".join(cells)

    status_label = {"active": "Forward test active", "test_complete": "Forward test complete"}.get(status, status)

    kpis = [
        ("Current equity", money(stats["current_equity"]), ""),
        ("Realized P/L", money(stats["realized_pnl"], sign=True), ""),
        ("Unrealized P/L", money(stats["unrealized_pnl"], sign=True), ""),
        ("Gross short exposure", money(stats["gross_exposure"]),
         f"cap {money(config.MAX_GROSS_EXPOSURE)}"),
        ("Closed trades", str(stats["num_trades"]),
         f"{stats['winning_trades']}W / {stats['losing_trades']}L"),
        ("Max drawdown", f"{stats['max_drawdown_pct']:.1f}%", ""),
    ]
    kpi_html = "".join(
        f'<div class="kpi"><div class="kpilabel">{esc(label)}</div>'
        f'<div class="kpival mono">{esc(val)}</div>'
        + (f'<div class="sub">{esc(sub)}</div>' if sub else "")
        + "</div>"
        for label, val, sub in kpis
    )

    return f"""<title>IPO Failure Desk</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans+Condensed:wght@500;600&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap">
<style>
:root {{
  --bg: #F6F5F1; --surface: #FFFFFF; --ink: #1C1B17; --muted: #6E6A5F;
  --line: #E2DFD6; --accent: #B3223C; --accent-soft: #F6E7EA;
  --good: #1E7F6B; --good-soft: #E4F0EC; --amber: #A66A00; --amber-soft: #F5EDDC;
  --mut-soft: #ECEAE3;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg: #15171B; --surface: #1D2025; --ink: #EBE9E2; --muted: #9A968B;
    --line: #2E323A; --accent: #E05C72; --accent-soft: #3A2229;
    --good: #45A98E; --good-soft: #1E3129; --amber: #D9A03F; --amber-soft: #33290F;
    --mut-soft: #272B31;
  }}
}}
:root[data-theme="dark"] {{
  --bg: #15171B; --surface: #1D2025; --ink: #EBE9E2; --muted: #9A968B;
  --line: #2E323A; --accent: #E05C72; --accent-soft: #3A2229;
  --good: #45A98E; --good-soft: #1E3129; --amber: #D9A03F; --amber-soft: #33290F;
  --mut-soft: #272B31;
}}
body {{ background: var(--bg); color: var(--ink); margin: 0;
  font: 15px/1.55 "IBM Plex Sans", system-ui, sans-serif; }}
.wrap {{ max-width: 1080px; margin: 0 auto; padding: 28px 20px 56px; }}
.mono {{ font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-variant-numeric: tabular-nums; }}
.strong {{ font-weight: 600; }}
.sub {{ color: var(--muted); font-size: 12.5px; }}
.num {{ text-align: right; }}
header {{ display: flex; flex-wrap: wrap; align-items: baseline; gap: 10px 16px;
  border-bottom: 2px solid var(--ink); padding-bottom: 14px; margin-bottom: 20px; }}
h1 {{ font-family: "IBM Plex Sans Condensed", "IBM Plex Sans", sans-serif;
  font-size: 26px; font-weight: 600; letter-spacing: .01em; margin: 0;
  text-wrap: balance; }}
h1 .v {{ color: var(--muted); font-weight: 500; }}
h2 {{ font-family: "IBM Plex Sans Condensed", sans-serif; font-size: 13px;
  font-weight: 600; letter-spacing: .09em; text-transform: uppercase;
  color: var(--muted); margin: 0 0 10px; }}
.pill {{ display: inline-block; padding: 2px 9px; border-radius: 999px;
  font: 600 11.5px/1.6 "IBM Plex Sans Condensed", sans-serif;
  letter-spacing: .05em; text-transform: uppercase; white-space: nowrap; }}
.pill-short {{ background: var(--accent-soft); color: var(--accent); }}
.pill-good {{ background: var(--good-soft); color: var(--good); }}
.pill-amber {{ background: var(--amber-soft); color: var(--amber); }}
.pill-mut {{ background: var(--mut-soft); color: var(--muted); }}
.meta {{ margin-left: auto; display: flex; gap: 8px; align-items: center; }}
.kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px; margin-bottom: 22px; }}
.kpi {{ background: var(--surface); border: 1px solid var(--line);
  padding: 12px 14px; }}
.kpilabel {{ font: 600 11px/1.5 "IBM Plex Sans Condensed", sans-serif;
  letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }}
.kpival {{ font-size: 22px; font-weight: 600; margin-top: 2px; }}
.cols {{ display: grid; grid-template-columns: 3fr 2fr; gap: 22px; }}
@media (max-width: 800px) {{ .cols {{ grid-template-columns: 1fr; }} }}
section {{ margin-bottom: 26px; }}
.tablewrap {{ overflow-x: auto; background: var(--surface);
  border: 1px solid var(--line); }}
table {{ border-collapse: collapse; width: 100%; font-size: 13.5px; }}
th {{ text-align: left; font: 600 11px/1.4 "IBM Plex Sans Condensed", sans-serif;
  letter-spacing: .08em; text-transform: uppercase; color: var(--muted);
  padding: 10px 12px; border-bottom: 1px solid var(--line); }}
th.num {{ text-align: right; }}
td {{ padding: 9px 12px; border-bottom: 1px solid var(--line);
  vertical-align: top; }}
tr:last-child td {{ border-bottom: 0; }}
.scorecard, .ticket {{ background: var(--surface); border: 1px solid var(--line);
  padding: 14px 16px; margin-bottom: 12px; }}
.scorehead, .tickethead {{ display: flex; justify-content: space-between;
  align-items: center; gap: 10px; margin-bottom: 8px; font-size: 14px; }}
.signals {{ list-style: none; margin: 0; padding: 0; font-size: 13px; }}
.signals li {{ display: flex; justify-content: space-between; gap: 12px;
  padding: 4px 0; border-bottom: 1px dashed var(--line); }}
.signals li:last-child {{ border-bottom: 0; }}
.signals .miss {{ color: var(--muted); }}
.signals .hit span:last-child {{ color: var(--accent); font-weight: 600; }}
.ticket p {{ margin: 8px 0 0; font-size: 13.5px; }}
.grid2 {{ display: grid; grid-template-columns: auto 1fr; gap: 3px 18px;
  font-size: 13px; }}
.tracker {{ display: grid; grid-template-columns: repeat(10, 1fr); gap: 4px; }}
.daycell {{ border: 1px solid var(--line); background: var(--surface);
  padding: 6px 4px; text-align: center; font-size: 11px; color: var(--muted);
  display: grid; gap: 2px; }}
.daycell.done {{ border-color: var(--accent); color: var(--ink);
  box-shadow: inset 0 3px 0 var(--accent); }}
.rules {{ font-size: 13px; margin: 0; padding-left: 18px; }}
.rules li {{ margin-bottom: 4px; }}
.log {{ background: var(--surface); border: 1px solid var(--line);
  border-left: 3px solid var(--accent); padding: 12px 16px; font-size: 13.5px; }}
footer {{ margin-top: 30px; color: var(--muted); font-size: 12.5px;
  border-top: 1px solid var(--line); padding-top: 12px; }}
</style>
<div class="wrap">
<header>
  <h1>IPO Failure Desk <span class="v">v{esc(config.STRATEGY_VERSION)}</span></h1>
  <div class="meta">
    <span class="pill pill-amber">Sandbox · paper</span>
    <span class="pill {'pill-good' if status == 'active' else 'pill-mut'}">{esc(status_label)}</span>
    <span class="mono sub">day {day_n} / {total_days} · through {esc(last_day)}</span>
  </div>
</header>

<div class="kpis">{kpi_html}</div>

<div class="cols">
<div>
  <section>
    <h2>IPO screening</h2>
    <div class="tablewrap"><table>
      <thead><tr><th>Ticker</th><th>Company</th><th>IPO date</th>
      <th class="num">IPO px</th><th class="num">D1 close</th>
      <th class="num">Score</th><th>Status</th></tr></thead>
      <tbody>{screening}</tbody>
    </table></div>
  </section>
  <section>
    <h2>Failure score breakdown</h2>
    {breakdown_html}
  </section>
</div>
<div>
  <section>
    <h2>Positions &amp; pending orders</h2>
    {tickets_html}
  </section>
  <section>
    <h2>Forward test — {total_days} trading days</h2>
    <div class="tracker">{tracker}</div>
  </section>
  <section>
    <h2>Standing rules</h2>
    <ul class="rules">
      <li>Qualify at score ≥{config.MIN_QUALIFYING_SCORE} <em>and</em> one technical failure signal.</li>
      <li>{money(config.POSITION_NOTIONAL)} per short · max {config.MAX_POSITIONS} positions · {money(config.MAX_GROSS_EXPOSURE)} gross cap.</li>
      <li>Stop +{config.STOP_PCT:.0%} · T1 −{config.TARGET1_PCT:.0%} covers half, stop to entry · T2 −{config.TARGET2_PCT:.0%}.</li>
      <li>Time stop {config.TIME_STOP_TRADING_DAYS} trading days · slippage {config.SLIPPAGE_PCT:.1%} per fill · borrow {config.BORROW_RATE_ANNUAL:.0%}/yr.</li>
      <li>Ambiguous intraday ordering: the stop is assumed to have hit first.</li>
      <li>No hindsight; unknown data scores zero points.</li>
    </ul>
  </section>
</div>
</div>

<section>
  <h2>Latest daily log — {esc(last_day)}</h2>
  <div class="log">{esc(state.meta.get('last_notes', 'See reports/ for the full daily record.'))}</div>
</section>

<footer>Paper trading only — $0 live capital. Regenerated from
<span class="mono">sandbox_data/state.json</span> by <span class="mono">dashboard.py</span>
after each processed trading day. Full history in <span class="mono">reports/</span>.</footer>
</div>
"""


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "dashboard.html"
    state = SandboxState.load()
    with open(out, "w") as f:
        f.write(render(state))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
