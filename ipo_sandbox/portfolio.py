"""Portfolio statistics (build.md sections 36-39)."""

from . import config


def compute_stats(positions: list, marks: dict, equity_history: list) -> dict:
    """positions: list[Position] (open and closed).
    marks: {ticker: last_price} for open positions.
    equity_history: list of {"date", "equity"} snapshots (chronological).
    """
    realized = sum(p.realized_net() for p in positions)
    unrealized = 0.0
    gross_exposure = 0.0
    for p in positions:
        if p.open and p.remaining_fraction > 0:
            mark = marks.get(p.ticker, p.entry_price_raw)
            unrealized += p.unrealized_net(mark)
            gross_exposure += mark * p.remaining_shares

    equity = config.STARTING_CAPITAL + realized + unrealized

    closed = [p for p in positions if not p.open]
    trade_nets = [p.realized_net() for p in closed]
    winners = [n for n in trade_nets if n > 0]
    losers = [n for n in trade_nets if n <= 0]

    gross_profits = sum(n for n in trade_nets if n > 0)
    gross_losses = -sum(n for n in trade_nets if n < 0)

    win_rate = len(winners) / len(trade_nets) if trade_nets else None
    avg_win = gross_profits / len(winners) if winners else None
    avg_loss = gross_losses / len(losers) if losers else None
    profit_factor = (gross_profits / gross_losses) if gross_losses > 0 else None

    expectancy = None
    if trade_nets:
        expectancy = sum(trade_nets) / len(trade_nets)

    # Max drawdown from the equity snapshot history (including current equity).
    curve = [e["equity"] for e in equity_history] + [equity]
    peak = curve[0] if curve else config.STARTING_CAPITAL
    max_dd = 0.0
    for v in curve:
        peak = max(peak, v)
        if peak > 0:
            max_dd = max(max_dd, (peak - v) / peak)

    holding = [p.trading_days_held for p in closed]

    return {
        "starting_equity": config.STARTING_CAPITAL,
        "current_equity": round(equity, 2),
        "realized_pnl": round(realized, 2),
        "unrealized_pnl": round(unrealized, 2),
        "gross_exposure": round(gross_exposure, 2),
        "net_exposure": round(-gross_exposure, 2),  # short-only book
        "num_trades": len(trade_nets),
        "winning_trades": len(winners),
        "losing_trades": len(losers),
        "win_rate": round(win_rate, 4) if win_rate is not None else None,
        "average_winner": round(avg_win, 2) if avg_win is not None else None,
        "average_loser": round(avg_loss, 2) if avg_loss is not None else None,
        "expectancy_per_trade": round(expectancy, 2) if expectancy is not None else None,
        "profit_factor": round(profit_factor, 2) if profit_factor is not None else None,
        "max_drawdown_pct": round(max_dd * 100, 2),
        "largest_winner": round(max(winners), 2) if winners else None,
        "largest_loser": round(min(losers), 2) if losers else None,
        "avg_holding_days": round(sum(holding) / len(holding), 1) if holding else None,
        "return_on_initial_capital_pct": round(
            (equity - config.STARTING_CAPITAL) / config.STARTING_CAPITAL * 100, 2
        ),
    }
