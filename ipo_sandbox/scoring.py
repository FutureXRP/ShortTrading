"""IPO Failure Score (build.md sections 9-18).

Unknown data never adds points: the no-hindsight rule means we only score
what we actually know at decision time, and missing data biases against
taking the trade.
"""

from . import config
from .models import IPOCandidate


def compute_score(c: IPOCandidate) -> dict:
    """Return score breakdown for a candidate given the bars observed so far."""
    signals = {}

    # --- Fundamental signals ---
    signals["unprofitable"] = (
        config.SCORE_UNPROFITABLE if c.profitable is False else 0
    )
    signals["revenue_below_100m"] = (
        config.SCORE_REVENUE_BELOW_100M
        if c.revenue is not None and c.revenue < config.REVENUE_THRESHOLD
        else 0
    )

    # --- Valuation signal ---
    valuation_flag = False
    if c.market_cap is not None and c.revenue is not None:
        if c.revenue <= 0:
            valuation_flag = c.market_cap > 0  # no revenue = effectively infinite multiple
        else:
            valuation_flag = (c.market_cap / c.revenue) > config.VALUATION_MULTIPLE_THRESHOLD
    signals["valuation_above_10x"] = config.SCORE_VALUATION_ABOVE_10X if valuation_flag else 0

    # --- Offering quality (one point max: priced weak OR downsized) ---
    priced_weak = False
    if c.range_low is not None and c.range_high is not None:
        midpoint = (c.range_low + c.range_high) / 2.0
        priced_weak = c.ipo_price < midpoint
    signals["weak_offering"] = (
        config.SCORE_WEAK_OFFERING if (priced_weak or c.downsized) else 0
    )

    # --- Insider selling ---
    signals["secondary_above_30pct"] = (
        config.SCORE_SECONDARY_ABOVE_30PCT
        if c.secondary_pct is not None and c.secondary_pct > config.SECONDARY_SHARE_THRESHOLD
        else 0
    )

    # --- Technical signals ---
    day1 = c.bar_for_day(1)
    day2 = c.bar_for_day(2)

    day1_reject = day1 is not None and day1.close < c.ipo_price
    signals["day1_close_below_ipo"] = (
        config.SCORE_DAY1_CLOSE_BELOW_IPO if day1_reject else 0
    )

    day2_breakdown = day1 is not None and day2 is not None and day2.close < day1.low
    signals["day2_close_below_day1_low"] = (
        config.SCORE_DAY2_CLOSE_BELOW_DAY1_LOW if day2_breakdown else 0
    )

    volume_decline = day1 is not None and day2 is not None and day2.volume < day1.volume
    signals["day2_volume_below_day1"] = (
        config.SCORE_DAY2_VOLUME_BELOW_DAY1 if volume_decline else 0
    )

    total = sum(signals.values())

    # Qualification (section 18): score >= 5 AND at least one technical *failure*
    # signal. Declining volume alone does not trigger a trade (section 16), so
    # the technical requirement is met only by day-1 rejection or day-2 breakdown.
    has_technical_failure = day1_reject or day2_breakdown

    return {
        "signals": signals,
        "total": total,
        "has_technical_failure": has_technical_failure,
        "qualifies": (
            not c.excluded
            and total >= config.MIN_QUALIFYING_SCORE
            and has_technical_failure
        ),
    }
