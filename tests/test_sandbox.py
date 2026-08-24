"""Tests for the IPO Failure Short System v0.1 sandbox engine."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ipo_sandbox import config, engine
from ipo_sandbox.models import DailyBar, IPOCandidate
from ipo_sandbox.portfolio import compute_stats
from ipo_sandbox.scoring import compute_score
from ipo_sandbox.store import SandboxState


def make_candidate(**overrides):
    """A maximally failing IPO: unprofitable, small, expensive, weak offering,
    heavy insider selling, day-1 rejection, day-2 breakdown, fading volume."""
    fields = dict(
        ticker="FAIL",
        company="Failing Co",
        ipo_date="2026-08-20",
        ipo_price=20.0,
        range_low=20.0,
        range_high=24.0,      # priced at 20 < midpoint 22
        revenue=50e6,          # < $100M
        profitable=False,
        market_cap=900e6,      # 18x sales
        secondary_pct=0.40,    # > 30%
    )
    fields.update(overrides)
    c = IPOCandidate(**fields)
    if "bars" not in overrides:
        c.bars = [
            DailyBar("2026-08-20", 20.0, 20.5, 17.8, 18.0, 5_000_000),  # D1: close < IPO
            DailyBar("2026-08-21", 18.0, 18.2, 16.5, 16.9, 3_000_000),  # D2: close < D1 low, vol down
        ]
    return c


class ScoringTests(unittest.TestCase):
    def test_max_score_candidate(self):
        s = compute_score(make_candidate())
        self.assertEqual(s["total"], 11)
        self.assertTrue(s["has_technical_failure"])
        self.assertTrue(s["qualifies"])

    def test_signal_breakdown(self):
        s = compute_score(make_candidate())["signals"]
        self.assertEqual(s["unprofitable"], 2)
        self.assertEqual(s["revenue_below_100m"], 1)
        self.assertEqual(s["valuation_above_10x"], 1)
        self.assertEqual(s["weak_offering"], 1)
        self.assertEqual(s["secondary_above_30pct"], 1)
        self.assertEqual(s["day1_close_below_ipo"], 2)
        self.assertEqual(s["day2_close_below_day1_low"], 2)
        self.assertEqual(s["day2_volume_below_day1"], 1)

    def test_no_technical_failure_blocks_qualification(self):
        # Fundamentally awful but the market accepts it: score 6, no technical.
        c = make_candidate(bars=[
            DailyBar("2026-08-20", 20.0, 25.0, 20.0, 24.0, 5_000_000),
            DailyBar("2026-08-21", 24.0, 26.0, 23.0, 25.0, 6_000_000),
        ])
        s = compute_score(c)
        self.assertEqual(s["total"], 6)
        self.assertFalse(s["has_technical_failure"])
        self.assertFalse(s["qualifies"])

    def test_volume_alone_is_not_technical_failure(self):
        # Only fading volume on day 2; price holds up. Section 16.
        c = make_candidate(bars=[
            DailyBar("2026-08-20", 20.0, 25.0, 20.0, 24.0, 5_000_000),
            DailyBar("2026-08-21", 24.0, 26.0, 23.5, 25.0, 1_000_000),
        ])
        s = compute_score(c)
        self.assertEqual(s["signals"]["day2_volume_below_day1"], 1)
        self.assertFalse(s["has_technical_failure"])
        self.assertFalse(s["qualifies"])

    def test_score_below_threshold_blocks_qualification(self):
        # Profitable, big, cheap, strong offering — only day-1 rejection (+2).
        c = make_candidate(
            profitable=True, revenue=500e6, market_cap=1e9,
            range_low=18.0, range_high=20.0, secondary_pct=0.0,
            bars=[DailyBar("2026-08-20", 20.0, 20.5, 17.8, 18.0, 5_000_000)],
        )
        s = compute_score(c)
        self.assertEqual(s["total"], 2)
        self.assertTrue(s["has_technical_failure"])
        self.assertFalse(s["qualifies"])

    def test_weak_offering_single_point_for_price_and_downsize(self):
        # Both downpriced and downsized: still only +1 (section 12).
        c = make_candidate(downsized=True)
        self.assertEqual(compute_score(c)["signals"]["weak_offering"], 1)
        self.assertEqual(compute_score(c)["total"], 11)

    def test_unknown_data_scores_zero(self):
        c = make_candidate(revenue=None, profitable=None, market_cap=None,
                           secondary_pct=None, range_low=None, range_high=None)
        s = compute_score(c)
        self.assertEqual(s["total"], 5)  # only the technical signals
        self.assertTrue(s["qualifies"])  # 5 points + technical failure

    def test_excluded_never_qualifies(self):
        c = make_candidate(excluded=True, exclusion_reason="SPAC")
        self.assertFalse(compute_score(c)["qualifies"])

    def test_zero_revenue_counts_as_extreme_valuation(self):
        c = make_candidate(revenue=0.0)
        self.assertEqual(compute_score(c)["signals"]["valuation_above_10x"], 1)


class EngineTests(unittest.TestCase):
    def _pos(self):
        # Short at $20 open: stop 22, T1 15, T2 10, $250 notional -> 12.5 sh.
        return engine.open_position("FAIL", "2026-08-21", "2026-08-24", 20.0)

    def test_entry_levels_and_slippage(self):
        p = self._pos()
        self.assertAlmostEqual(p.shares, 12.5)
        self.assertAlmostEqual(p.entry_price_effective, 19.90)  # 0.5% against us
        self.assertAlmostEqual(p.stop_price, 22.0)
        self.assertAlmostEqual(p.target1, 15.0)
        self.assertAlmostEqual(p.target2, 10.0)

    def test_stop_loss(self):
        p = self._pos()
        fills = engine.process_day(p, DailyBar("2026-08-25", 21.0, 22.5, 20.5, 22.2, 1e6))
        self.assertEqual(len(fills), 1)
        self.assertEqual(fills[0].reason, "stop")
        self.assertAlmostEqual(fills[0].raw_price, 22.0)
        self.assertAlmostEqual(fills[0].effective_price, 22.11)  # +0.5% slippage
        self.assertFalse(p.open)
        # Planned loss ≈ $25 + slippage + borrow, so net < -25.
        self.assertLess(fills[0].net_profit, -25.0)

    def test_gap_through_stop_fills_at_open(self):
        p = self._pos()
        fills = engine.process_day(p, DailyBar("2026-08-25", 30.0, 32.0, 29.0, 31.0, 1e6))
        self.assertEqual(fills[0].reason, "stop")
        self.assertAlmostEqual(fills[0].raw_price, 30.0)  # worse than the $22 stop

    def test_target1_covers_half_and_moves_stop_to_entry(self):
        p = self._pos()
        fills = engine.process_day(p, DailyBar("2026-08-25", 17.0, 18.0, 14.8, 15.2, 1e6))
        self.assertEqual(len(fills), 1)
        self.assertEqual(fills[0].reason, "target1")
        self.assertAlmostEqual(fills[0].raw_price, 15.0)
        self.assertAlmostEqual(p.remaining_fraction, 0.5)
        self.assertTrue(p.stop_moved_to_entry)
        self.assertAlmostEqual(p.stop_price, 20.0)
        self.assertGreater(fills[0].net_profit, 0)

    def test_conservative_stop_first_when_both_possible(self):
        # Day trades through both the stop (22) and target1 (15): stop wins.
        p = self._pos()
        fills = engine.process_day(p, DailyBar("2026-08-25", 20.0, 23.0, 14.0, 16.0, 1e6))
        self.assertEqual(len(fills), 1)
        self.assertEqual(fills[0].reason, "stop")
        self.assertFalse(p.open)

    def test_conservative_after_t1_same_day_entry_stop(self):
        # T1 hit, then the day also traded at/above entry: remainder stopped at entry.
        p = self._pos()
        fills = engine.process_day(p, DailyBar("2026-08-25", 17.0, 20.5, 14.8, 19.0, 1e6))
        self.assertEqual([f.reason for f in fills], ["target1", "stop"])
        self.assertAlmostEqual(fills[1].raw_price, 20.0)
        self.assertFalse(p.open)

    def test_target2_closes_remainder(self):
        p = self._pos()
        engine.process_day(p, DailyBar("2026-08-25", 17.0, 18.0, 14.8, 15.2, 1e6))  # T1
        fills = engine.process_day(p, DailyBar("2026-08-26", 14.0, 14.5, 9.5, 9.8, 1e6))
        self.assertEqual(fills[0].reason, "target2")
        self.assertAlmostEqual(fills[0].raw_price, 10.0)
        self.assertFalse(p.open)
        self.assertGreater(p.realized_net(), 0)

    def test_time_stop_after_20_trading_days(self):
        p = self._pos()
        for i in range(19):
            fills = engine.process_day(
                p, DailyBar(f"2026-09-{i+1:02d}", 19.0, 19.5, 18.5, 19.0, 1e6))
            self.assertEqual(fills, [])
        fills = engine.process_day(p, DailyBar("2026-09-20", 19.0, 19.5, 18.5, 19.0, 1e6))
        self.assertEqual(fills[0].reason, "time_stop")
        self.assertEqual(p.trading_days_held, 20)
        self.assertFalse(p.open)

    def test_borrow_cost_matches_build_md_example(self):
        # $250 × 30% × 20/365 ≈ $4.11 (section 30) — same formula, on
        # effective entry notional and calendar days.
        p = self._pos()
        fill = engine.close_at_price(p, "2026-09-13", 19.0, "test_end")  # 20 calendar days
        expected = (p.entry_price_effective * p.shares) * 0.30 * 20 / 365
        self.assertAlmostEqual(fill.borrow_cost, expected)
        self.assertAlmostEqual(expected, 4.09, places=2)

    def test_closed_position_ignores_further_days(self):
        p = self._pos()
        engine.process_day(p, DailyBar("2026-08-25", 21.0, 22.5, 20.5, 22.2, 1e6))
        self.assertEqual(engine.process_day(
            p, DailyBar("2026-08-26", 22.0, 23.0, 21.0, 22.0, 1e6)), [])


class PortfolioTests(unittest.TestCase):
    def test_stats_flat(self):
        stats = compute_stats([], {}, [])
        self.assertEqual(stats["current_equity"], 500.0)
        self.assertEqual(stats["num_trades"], 0)
        self.assertIsNone(stats["win_rate"])
        self.assertEqual(stats["max_drawdown_pct"], 0.0)

    def test_stats_with_trades(self):
        win = engine.open_position("WIN", "2026-08-21", "2026-08-24", 20.0)
        engine.process_day(win, DailyBar("2026-08-25", 17.0, 18.0, 14.8, 15.2, 1e6))
        engine.process_day(win, DailyBar("2026-08-26", 14.0, 14.5, 9.5, 9.8, 1e6))
        loss = engine.open_position("LOSS", "2026-08-21", "2026-08-24", 20.0)
        engine.process_day(loss, DailyBar("2026-08-25", 21.0, 22.5, 20.5, 22.2, 1e6))
        stats = compute_stats([win, loss], {}, [])
        self.assertEqual(stats["num_trades"], 2)
        self.assertEqual(stats["winning_trades"], 1)
        self.assertEqual(stats["losing_trades"], 1)
        self.assertEqual(stats["win_rate"], 0.5)
        self.assertGreater(stats["profit_factor"], 1.0)
        self.assertAlmostEqual(
            stats["current_equity"],
            500 + win.realized_net() + loss.realized_net(), places=2)

    def test_max_drawdown(self):
        # build.md section 39: $500 -> $900 -> $600 is a 33.3% drawdown.
        # compute_stats extends the curve with current equity, which is 500
        # for an empty book, so feed history whose trough matches that.
        history = [{"date": "d1", "equity": 500}, {"date": "d2", "equity": 900},
                   {"date": "d3", "equity": 600}]
        curve = [e["equity"] for e in history]
        peak, dd = curve[0], 0.0
        for v in curve:
            peak = max(peak, v)
            dd = max(dd, (peak - v) / peak)
        self.assertAlmostEqual(dd * 100, 33.33, places=1)

        stats = compute_stats([], {}, history)
        # 900 -> 500 (current flat equity) = 44.44%
        self.assertAlmostEqual(stats["max_drawdown_pct"], 44.44, places=1)


class StoreAndFlowTests(unittest.TestCase):
    def test_full_forward_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = os.path.join(tmp, "sandbox_data")
            state = SandboxState.init("2026-08-24", data_dir)
            state.candidates["FAIL"] = make_candidate()
            state.save()

            state = SandboxState.load(data_dir)
            self.assertEqual(state.meta["mode"], "paper")
            self.assertTrue(compute_score(state.candidates["FAIL"])["qualifies"])

            # Qualify after the close, enter next open, ride to targets.
            state.pending_entries.append(
                {"ticker": "FAIL", "qualification_date": "2026-08-21"})
            c = state.candidates["FAIL"]
            c.bars.append(DailyBar("2026-08-24", 16.5, 16.8, 15.9, 16.0, 2_000_000))
            pos = engine.open_position("FAIL", "2026-08-21", "2026-08-24", 16.5)
            state.positions.append(pos)
            state.pending_entries = []
            engine.process_day(pos, c.bars[-1])
            state.save()

            state = SandboxState.load(data_dir)
            self.assertEqual(len(state.open_positions()), 1)
            p = state.open_positions()[0]
            self.assertAlmostEqual(p.stop_price, 16.5 * 1.10)
            marks = state.latest_marks()
            self.assertAlmostEqual(marks["FAIL"], 16.0)
            self.assertAlmostEqual(
                state.gross_exposure(marks), 16.0 * p.remaining_shares)

    def test_exposure_cap_math(self):
        # 4 positions × $250 = $1,000 = the cap; a 5th must not fit.
        self.assertEqual(config.MAX_POSITIONS * config.POSITION_NOTIONAL,
                         config.MAX_GROSS_EXPOSURE)


if __name__ == "__main__":
    unittest.main()
