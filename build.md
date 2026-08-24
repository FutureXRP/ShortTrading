# IPO Failure Short System

**Version:** 0.1 — Sandbox
**Status:** Forward Testing
**Initial Paper Capital:** $500
**Initial Maximum Exposure:** $1,000
**Strategy Type:** Systematic IPO Failure / Short-Side
**Primary Objective:** Identify newly public companies showing fundamental and technical signs of failure and establish defined-risk bearish positions.

---

# 1. Executive Summary

The IPO Failure Short System is a systematic trading strategy designed around a simple hypothesis:

> Newly public companies displaying both fundamental weakness and immediate market rejection may have a statistically favorable probability of declining substantially after their IPO.

The system does **not** blindly short every IPO.

Historical research shows that although a large percentage of IPOs eventually decline substantially from their first-day closing prices, a minority produce extraordinary gains.

Those extreme winners make indiscriminate short selling dangerous because:

* Long positions have limited downside.
* Short positions have theoretically unlimited downside.
* IPOs frequently have small public floats.
* Borrow availability can be limited.
* Borrow rates can be extremely high.
* IPOs can experience violent short squeezes.
* A few extreme winners can overwhelm profits from many successful shorts.

Therefore, the system attempts to identify **failed IPOs** rather than simply **new IPOs**.

The core process is:

**IPO → Observe → Score → Confirm Failure → Enter → Manage Risk → Exit → Record → Analyze**

---

# 2. Development Roadmap

The system will be developed in stages.

## Phase 1 — Historical Research

Analyze historical IPO behavior to determine whether a persistent short-side opportunity exists.

Questions include:

* How frequently do IPOs decline?
* How frequently do IPOs decline more than 25%?
* How frequently do IPOs decline more than 50%?
* Which characteristics predict poor aftermarket performance?
* Which IPOs become extreme winners?
* What characteristics distinguish failed IPOs from successful IPOs?

Historical research suggests that IPO underperformance is concentrated disproportionately among weaker companies.

Particularly interesting characteristics include:

* Unprofitable businesses
* Small revenue bases
* Extreme valuations
* Weak offering demand
* Immediate aftermarket rejection
* Heavy insider selling

---

# 3. Phase 2 — Forward Sandbox

The strategy begins with:

**Paper Capital: $500**

No real money is used.

The sandbox runs prospectively using only information that would have been available when each simulated trading decision occurred.

No hindsight is permitted.

No trades may be retroactively inserted.

The first forward-testing period is:

**10 U.S. trading days**

At the conclusion of the test, the strategy will be evaluated and potentially revised.

---

# 4. Phase 3 — Extended Paper Trading

If the initial sandbox demonstrates potential, the system moves into extended paper trading.

Target testing period:

**30–90 trading days**

The objective is to determine whether the apparent edge survives:

* Different market conditions
* Different IPO sectors
* Different volatility environments
* Hot IPO markets
* Weak IPO markets
* High-interest-rate environments
* Risk-on environments
* Risk-off environments

---

# 5. Phase 4 — Broker-Integrated Paper System

If the strategy survives extended testing, the system may be connected to a brokerage API operating exclusively in paper-trading mode.

Potential capabilities:

* Automatic IPO detection
* Fundamental data retrieval
* Price monitoring
* Failure Score calculation
* Borrow availability checks
* Entry generation
* Stop generation
* Target generation
* Position sizing
* Portfolio risk monitoring
* Automated journaling
* Performance analytics

---

# 6. Phase 5 — Live Capital

Live trading will only be considered after the system demonstrates a statistically meaningful edge under realistic assumptions.

Live deployment should begin with minimal capital.

The strategy must never assume that historical or paper-trading profitability guarantees future profitability.

---

# 7. Eligible Securities

The universe consists primarily of newly listed U.S. operating-company IPOs.

Eligible securities should generally be:

* Newly public operating companies
* Listed on a major U.S. exchange
* Genuine initial public offerings
* Securities with sufficient price and volume information

---

# 8. Excluded Securities

The following are excluded:

* SPACs
* Blank-check companies
* ETFs
* Closed-end funds
* Direct listings
* Units
* Warrants
* Rights offerings
* Secondary listings
* Companies already publicly traded elsewhere merely establishing a U.S. ADS/ADR
* Securities without adequate market data
* Offerings that are not genuine operating-company IPOs

Additional exclusions may eventually include:

* Extremely illiquid stocks
* Securities without available borrow
* Securities with prohibitively expensive borrow
* Stocks subject to unusual trading restrictions

---

# 9. IPO Failure Score

Every qualifying IPO receives an **IPO Failure Score**.

The score combines fundamental, offering, and technical information.

Higher scores indicate greater evidence that the IPO is failing.

---

# 10. Fundamental Signals

## Unprofitable

**Score: +2**

The company reports a net loss based upon the latest available fiscal-year or trailing-twelve-month financial information.

Reason:

Historical IPO research suggests unprofitable companies significantly underperform profitable IPOs over longer periods.

---

## Revenue Below $100 Million

**Score: +1**

Latest annual or trailing revenue:

**< $100 million**

Reason:

Small companies tend to present greater operating and valuation risk.

The combination of:

**small + unprofitable**

is particularly interesting.

---

# 11. Valuation Signal

## IPO Valuation Greater Than 10× Sales

**Score: +1**

Approximate valuation:

**IPO market capitalization / annual revenue > 10**

Reason:

Extremely high sales multiples require substantial future growth.

If market enthusiasm disappears, valuation compression can produce significant declines.

Future versions should test additional thresholds:

* 5× sales
* 10× sales
* 20× sales
* 40× sales

These thresholds should be evaluated empirically rather than assumed.

---

# 12. Offering Quality Signals

## IPO Prices Below Marketed Range

**Score: +1**

Example:

Expected range:

**$20–$24**

Final IPO price:

**$18**

This indicates weaker-than-expected institutional demand.

---

## Materially Downsized Offering

**Score: +1**

A substantial reduction in shares offered may indicate weak demand.

If both price and size are reduced, the system currently awards only the defined offering-quality score unless future testing demonstrates that the two signals should be separated.

---

# 13. Insider Selling

## Secondary Shares Greater Than 30%

**Score: +1**

If more than 30% of shares offered are being sold by existing shareholders rather than issued by the company, the IPO receives an additional failure point.

Reason:

Large secondary offerings can indicate that insiders or existing investors are using the IPO as a liquidity event.

This does not automatically mean the company will fail.

It is simply one component of the total score.

---

# 14. Technical Failure Signals

Fundamentals alone do not trigger a trade.

The market must begin confirming the thesis.

---

## Day-1 Close Below IPO Price

**Score: +2**

Example:

IPO price:

**$20**

Day-1 close:

**$18**

This is a major rejection signal.

Institutional investors purchased shares at $20 and the public market immediately valued them below the offering price.

---

# 15. Day-2 Breakdown

## Day-2 Close Below Day-1 Low

**Score: +2**

This is one of the strongest technical failure signals.

Example:

Day-1 low:

**$17.80**

Day-2 close:

**$16.90**

The IPO is making a new low almost immediately after listing.

---

# 16. Declining Volume

## Day-2 Volume Below Day-1 Volume

**Score: +1**

Falling volume combined with declining price may indicate that initial IPO excitement is disappearing.

Volume alone does not trigger a trade.

---

# 17. Current Scoring Table

| Signal                                                           | Points |
| ---------------------------------------------------------------- | -----: |
| Unprofitable                                                     |     +2 |
| Revenue < $100M                                                  |     +1 |
| IPO valuation >10× sales                                         |     +1 |
| IPO priced below marketed midpoint/range or materially downsized |     +1 |
| Secondary shares >30%                                            |     +1 |
| Day-1 close below IPO price                                      |     +2 |
| Day-2 close below Day-1 low                                      |     +2 |
| Day-2 volume below Day-1                                         |     +1 |

Maximum theoretical score:

**11 points**

---

# 18. Trade Qualification

An IPO must score:

# **5+ Points**

AND

must demonstrate at least one technical failure signal.

Therefore:

> A fundamentally weak company cannot automatically be shorted simply because it looks expensive.

The market must begin validating the bearish thesis.

---

# 19. Current Entry Rule

Once an IPO qualifies:

**Enter synthetic short at the next trading day's opening price.**

Example:

Day 1 — IPO

Day 2 — breakdown occurs

After Day 2 close — system identifies qualification

Day 3 open — short entry

This prevents hindsight.

---

# 20. Starting Capital

Initial sandbox:

# **$500**

The objective is to determine whether a small account could theoretically compound using the strategy.

---

# 21. Position Size

Initial synthetic position:

# **$250 short exposure**

This represents:

**50% of initial account equity per position**

However, exposure and risk are not the same thing.

The position is protected by a predetermined stop.

---

# 22. Maximum Portfolio Exposure

Maximum simultaneous gross short exposure:

# **$1,000**

Relative to the original $500 account:

# **2× gross exposure**

Maximum simultaneous positions:

# **4**

Each position:

**Approximately $250**

---

# 23. Stop Loss

Initial stop:

# **10% above entry**

Example:

Entry:

**$20**

Stop:

**$22**

$250 position × 10% adverse movement:

**≈ $25 planned loss**

Therefore, approximate initial account risk per position:

# **5%**

This is intentionally aggressive because the sandbox begins with only $500.

A future live implementation may use substantially smaller percentage risk.

---

# 24. Why Stops Are Mandatory

Short selling has asymmetric risk.

A stock purchased for $20 can only fall $20.

A stock shorted at $20 could theoretically rise to:

* $40
* $60
* $100
* $200
* $500+

IPO squeezes can be particularly violent because the available public float may initially be small.

Therefore:

# **No naked unlimited-risk position is permitted by the system.**

---

# 25. Profit Target #1

When the stock declines:

# **25% from entry**

Cover:

# **50% of the position**

Example:

Entry:

**$20**

Target:

**$15**

Half of the short is covered.

---

# 26. Stop Adjustment

After Target #1 is reached:

The stop on the remaining position moves to approximately:

# **Entry Price**

The objective is to prevent a profitable trade from becoming a significant loss.

---

# 27. Profit Target #2

Remaining position target:

# **50% decline from entry**

Example:

Entry:

**$20**

Final target:

**$10**

If reached, the remaining position is covered.

---

# 28. Time Stop

Maximum holding period:

# **20 trading days**

If neither the final target nor stop is reached, the remaining position is closed.

Reason:

The system is designed primarily to capture **IPO failure momentum**, not maintain indefinite bearish investments.

Capital should eventually be recycled into newer opportunities.

---

# 29. Transaction Friction

A realistic simulation must include costs.

Current sandbox assumption:

# **0.5% slippage on entry and exit**

This intentionally penalizes the strategy.

Real-world execution may be better or worse.

---

# 30. Borrow Cost

Default synthetic borrow rate:

# **30% annualized**

Borrow cost is prorated based upon the number of days the position remains open.

Example:

$250 position

30% annual borrow rate

20-day holding period

Approximate borrow cost:

**$250 × 30% × 20 / 365 ≈ $4.11**

Actual IPO borrow rates may vary enormously.

Some IPOs may be:

* Easy to borrow
* Hard to borrow
* Extremely expensive to borrow
* Completely unavailable to short

Therefore, future live versions must retrieve actual borrow information.

---

# 31. Borrow Availability

Future versions should require:

**Shares available to borrow**

before generating a short trade.

Potential additional variables:

* Shares available
* Utilization
* Annualized borrow rate
* Changes in borrow availability
* Changes in borrow cost

Borrow-market stress may itself eventually become a signal.

---

# 32. Conservative Intraday Assumption

Daily OHLC data cannot always determine whether a stop or target occurred first.

If both occur during the same trading session and intraday ordering cannot be established:

# **Assume the stop occurred first.**

This intentionally biases the backtest against the strategy.

---

# 33. No Hindsight Rule

Every simulated decision must use only information available at that point in time.

Forbidden:

* Entering trades retroactively
* Using later earnings information
* Using later analyst reports
* Using later insider transactions
* Using future price behavior
* Changing a score because we know the eventual outcome

The sandbox must behave as though it were actually trading that day.

---

# 34. Strategy Versioning

Trading rules should not be changed during a test simply because a position loses.

Example:

**Version 0.1**

runs for the complete predetermined test period.

Afterward:

Results are analyzed.

Changes create:

**Version 0.2**

Then Version 0.2 receives its own forward test.

This reduces curve-fitting.

---

# 35. Daily Sandbox Report

Every trading day the system should record:

## IPO Screening

* New IPOs
* Ticker
* Company
* IPO price
* Day-1 close
* Day-1 high
* Day-1 low
* Day-1 volume
* Day-2 close
* Day-2 volume
* Revenue
* Profit/loss status
* Approximate IPO valuation
* Secondary-share percentage
* IPO Failure Score

## Trade Information

* Qualified?
* Entry date
* Entry price
* Position size
* Stop
* Target #1
* Target #2
* Borrow assumption
* Current price
* Unrealized P/L
* Realized P/L
* Holding period

---

# 36. Portfolio Statistics

The sandbox should continuously calculate:

* Starting equity
* Current equity
* Realized profit
* Unrealized profit
* Gross exposure
* Net exposure
* Number of trades
* Winning trades
* Losing trades
* Win rate
* Average winner
* Average loser
* Profit factor
* Maximum drawdown
* Largest winner
* Largest loser
* Average holding period
* Return on initial capital

---

# 37. Critical Metric — Expectancy

Win rate alone does not determine profitability.

The primary metric is:

# **Expectancy**

Simplified:

**Expectancy = (Win Rate × Average Win) − (Loss Rate × Average Loss)**

Example:

40% winners

Average winner:

**+$60**

60% losers

Average loser:

**−$25**

Expectancy:

**(.40 × $60) − (.60 × $25)**

= **$24 − $15**

= **+$9 per trade**

Despite losing more trades than it wins, the system would theoretically have positive expectancy.

---

# 38. Profit Factor

Another important measurement:

**Gross Profits / Gross Losses**

Desired:

**>1.0**

Interesting:

**>1.5**

Strong:

**>2.0**

Profit factor must be evaluated alongside sample size.

Five successful trades prove almost nothing.

Hundreds of trades provide much stronger evidence.

---

# 39. Maximum Drawdown

Maximum drawdown measures the largest decline from an account equity peak.

Example:

Account grows:

**$500 → $900**

Then falls:

**$900 → $600**

Maximum drawdown:

**33.3%**

A profitable strategy can still be unusable if drawdowns are too large.

---

# 40. Risk of Ruin

The system should eventually estimate:

# **Probability of account failure**

This is especially important because the initial $500 sandbox uses aggressive percentage risk.

A strategy capable of:

**$500 → $10,000**

is unattractive if historical simulations show a 40% probability of:

**$500 → $0**

Survival matters more than theoretical maximum return.

---

# 41. Potential Put-Option Version

A second version of the strategy may use put options instead of conventional short positions.

Potential advantages:

* Defined maximum loss
* No unlimited short exposure
* No stock borrow requirement
* Built-in leverage
* Ability to benefit from large downside moves

Potential disadvantages:

* Expensive implied volatility
* Wide bid/ask spreads
* Time decay
* Limited strike availability
* Limited expiration availability
* Options may not become available immediately after IPO
* Volatility collapse can hurt option value

This strategy should be tested independently.

---

# 42. Proposed Put Strategy

Potential structure:

**IPO Failure Score ≥5**

*

**Technical failure confirmed**

*

**Options available**

Then evaluate:

* 30–60 DTE puts
* ATM puts
* Slightly ITM puts
* Slightly OTM puts
* Put spreads

Risk per trade could initially be:

# **$25–$50 premium**

Maximum loss:

**100% of premium paid**

No additional loss permitted.

---

# 43. Strategy Comparison

Eventually the system should compare:

### Strategy A

1× conventional short

### Strategy B

2× gross short exposure

### Strategy C

Defined-risk put options

### Strategy D

Put debit spreads

### Strategy E

Short positions combined with puts as protection

Performance should be compared using:

* CAGR
* Total return
* Maximum drawdown
* Sharpe-like risk-adjusted metrics
* Profit factor
* Risk of ruin
* Capital efficiency

---

# 44. Potential Future Signals

The following are research candidates and are **not yet active trading rules**.

## Day-1 VWAP Failure

Price closes below Day-1 VWAP.

---

## Opening Range Breakdown

Price breaks below the first:

* 15-minute range
* 30-minute range
* 60-minute range

---

## Failed Day-1 Rally

IPO initially rallies substantially but closes near its low.

Example:

IPO:

**$20**

Intraday high:

**$35**

Close:

**$22**

This may indicate severe distribution.

---

## Extreme Day-1 Pop

Potential signal:

**+50%, +100%, +200%**

However, historical analysis must determine whether this is actually bearish.

Extreme momentum can continue much longer than expected.

---

## Relative Volume Collapse

Day-2/Day-3 volume falls dramatically compared with Day 1.

---

## Institutional Underwriter Quality

Potential scoring based upon lead underwriter.

---

## Insider Lockup

Track:

* Lockup expiration date
* Shares becoming eligible for sale
* Insider ownership
* VC ownership
* Private-equity ownership

Potential second trade window:

# **IPO + ~180 Days**

---

# 45. Lockup Expiration Strategy

A separate strategy may eventually examine:

**Large insider ownership**

*

**Weak stock performance**

*

**Upcoming lockup expiration**

*

**Large number of shares becoming eligible for sale**

Potential trade:

Short ahead of or immediately following lockup expiration.

This must be independently tested.

---

# 46. Market Regime

IPO performance may depend heavily upon overall market conditions.

Future versions should track:

* S&P 500 trend
* Nasdaq trend
* Russell 2000 trend
* VIX
* Interest rates
* IPO issuance volume
* Average Day-1 IPO return
* Market breadth

Potential conclusion:

The IPO short strategy may perform significantly better during certain regimes.

---

# 47. IPO Market Temperature

Develop an eventual:

# **IPO Market Temperature Score**

Possible classifications:

**Cold**

**Neutral**

**Hot**

**Mania**

A hot IPO market may produce more extreme valuations but also greater squeeze risk.

A deteriorating IPO market may provide the strongest environment for the strategy.

---

# 48. Portfolio Scaling

If the system demonstrates positive expectancy, position size should scale with equity rather than remain permanently fixed.

Possible future rule:

**Risk 2–5% of current equity per position**

Example:

Account:

**$500**

5% risk:

**$25**

Account:

**$1,000**

5% risk:

**$50**

Account:

**$5,000**

5% risk:

**$250**

Account:

**$10,000**

5% risk:

**$500**

This creates compounding.

---

# 49. Compounding

The objective is not simply to earn money from individual IPOs.

The long-term objective is:

# **Compound a repeatable statistical edge**

If capital grows, position sizes increase according to predetermined risk rules.

The system must never increase risk merely because recent trades have been successful.

---

# 50. Drawdown Protection

Future versions should consider reducing risk during significant drawdowns.

Example:

Normal risk:

**5%**

After 15% portfolio drawdown:

**3%**

After 25% drawdown:

**2%**

After recovery:

Gradually return toward normal sizing.

This may substantially reduce risk of ruin.

---

# 51. Kill Switch

A live version should include an automatic strategy shutdown.

Potential triggers:

* Maximum daily loss exceeded
* Maximum weekly loss exceeded
* Maximum portfolio drawdown exceeded
* Market-data failure
* Broker API failure
* Incorrect position reconciliation
* Abnormal execution
* Borrow unexpectedly recalled
* Trading halt
* Regulatory issue
* Strategy behavior inconsistent with expected parameters

The system should fail safely.

---

# 52. Trading Halts

IPO trading halts are common.

During a halt:

**No assumption should be made about execution.**

Stops cannot necessarily protect the portfolio during a trading halt.

When trading resumes, price can gap substantially beyond the stop.

This represents one of the largest risks to shorting IPOs.

---

# 53. Gap Risk

Example:

Short:

**$20**

Stop:

**$22**

Stock halts.

Reopens:

**$30**

The $22 stop cannot guarantee a $22 exit.

Actual loss could be substantially greater.

Therefore:

# **A stop limits intended risk — not guaranteed risk.**

This must be incorporated into risk-of-ruin simulations.

---

# 54. Real-World Broker Requirements

Before live deployment, the system must verify:

* Margin eligibility
* Short-selling permission
* Borrow availability
* Borrow rate
* Maintenance margin
* Concentration requirements
* Day-trading restrictions where applicable
* Account equity requirements
* Order-type support
* API availability
* Market-data quality

---

# 55. System Architecture

Potential production architecture:

```text
IPO DATA FEED
      ↓
IPO UNIVERSE FILTER
      ↓
FUNDAMENTAL DATA
      ↓
OFFERING DATA
      ↓
MARKET DATA
      ↓
IPO FAILURE SCORE
      ↓
TECHNICAL CONFIRMATION
      ↓
RISK ENGINE
      ↓
POSITION SIZING
      ↓
TRADE SIGNAL
      ↓
BROKER / PAPER BROKER
      ↓
POSITION MONITOR
      ↓
STOP / TARGET ENGINE
      ↓
TRADE JOURNAL
      ↓
PERFORMANCE DATABASE
      ↓
ANALYTICS DASHBOARD
```

---

# 56. Data Required

Production system will eventually require:

## IPO Data

* IPO date
* IPO price
* Expected price range
* Shares offered
* Primary shares
* Secondary shares
* Underwriters
* Lockup information

## Fundamental Data

* Revenue
* Revenue growth
* Net income
* Free cash flow
* Cash
* Debt
* Shares outstanding
* Market capitalization

## Market Data

* Open
* High
* Low
* Close
* Volume
* VWAP
* Intraday candles

## Short Data

* Borrow availability
* Borrow rate
* Short interest
* Utilization

## Options Data

* Strikes
* Expirations
* Bid
* Ask
* Volume
* Open interest
* Implied volatility
* Greeks

---

# 57. Trade Database

Every signal should be permanently recorded.

Example schema:

```text
trade_id
ticker
company
ipo_date
ipo_price
failure_score
qualification_date
entry_date
entry_price
shares
notional
stop_price
target_1
target_2
borrow_rate
exit_date
exit_price
gross_profit
borrow_cost
slippage
net_profit
holding_days
maximum_favorable_excursion
maximum_adverse_excursion
exit_reason
strategy_version
```

This database becomes increasingly valuable as the system operates.

---

# 58. Machine Learning — Future Research

Machine learning should **not** be introduced until a sufficiently large clean dataset exists.

Eventually, the system could analyze whether combinations of variables predict IPO failure.

Potential features:

* Profitability
* Revenue
* Revenue growth
* IPO valuation
* Offer pricing
* Offering size
* Insider selling
* Day-1 return
* Day-1 range
* Day-1 volume
* Day-2 return
* Day-2 volume
* Sector
* Underwriter
* Market regime
* Borrow rate
* Short interest
* Lockup structure

Target variables could include:

**Probability of −25%**

**Probability of −50%**

**Probability of +50% squeeze**

The final variable is extremely important.

The system should predict not only:

> "How likely is this stock to collapse?"

but also:

> "How likely is this stock to explode against the short first?"

---

# 59. Ultimate Decision Engine

A mature system may eventually calculate three probabilities:

# P25

Probability stock declines ≥25%.

# P50

Probability stock declines ≥50%.

# PSQ

Probability stock experiences a dangerous short squeeze.

Trade only when:

**Expected downside opportunity substantially exceeds squeeze risk.**

---

# 60. Current Sandbox Rules — Version 0.1

For clarity, the complete current system is:

```text
STARTING CAPITAL
$500

ELIGIBLE
New U.S. operating-company IPOs

EXCLUDE
SPACs
Direct listings
Funds
ETFs
Units
Warrants
Non-genuine IPO listings

FAILURE SCORE

Unprofitable                         +2
Revenue < $100M                     +1
IPO valuation >10× sales            +1
Weak/downpriced offering            +1
Secondary shares >30%               +1
Day-1 close below IPO price         +2
Day-2 close below Day-1 low         +2
Day-2 volume below Day-1 volume     +1

QUALIFICATION
Score ≥5
AND
At least one technical failure signal

ENTRY
Next trading day's open

POSITION
$250 synthetic short

MAX POSITIONS
4

MAX GROSS EXPOSURE
$1,000

INITIAL STOP
10% above entry

APPROXIMATE INITIAL RISK
$25 per position

TARGET #1
25% stock decline
Cover 50%

AFTER TARGET #1
Move remaining stop to entry

TARGET #2
50% stock decline
Cover remainder

TIME EXIT
20 trading days

SLIPPAGE
0.5% entry and exit

BORROW COST
30% annualized default
unless actual contemporaneous rate is available

AMBIGUOUS DAILY PRICE ACTION
Assume stop occurred before target

NO HINDSIGHT
Strictly enforced

INITIAL TEST
10 trading days
```

---

# 61. Success Criteria

The first sandbox is not expected to prove the strategy.

It is intended to identify problems.

We want to learn:

* Are enough IPOs generated?
* Are enough trades generated?
* Does the scoring system discriminate?
* Are qualifying stocks actually weak?
* Are stops too tight?
* Are targets realistic?
* Are borrow costs destructive?
* Are qualifying stocks available to short?
* Does 2× exposure create excessive drawdown?
* Does the strategy produce positive expectancy?

---

# 62. Version 0.2

At the conclusion of Version 0.1:

Do **not** simply optimize for maximum historical profit.

Analyze:

* False positives
* False negatives
* Winning trades
* Losing trades
* Stocks that nearly qualified
* Stocks that squeezed
* Stocks that collapsed
* Borrow problems
* Execution problems

Then create Version 0.2.

Every rule change must have a reason.

---

# 63. Core Philosophy

The system is built around five principles.

## 1. Do Not Predict When You Can Confirm

We do not short simply because an IPO appears expensive.

Wait for market rejection.

## 2. Risk Comes Before Return

A strategy that occasionally destroys the account is not successful.

## 3. Let Large Failures Pay for Small Mistakes

The desired payoff structure is:

**Small controlled losses**

versus

**Occasional large winners**

## 4. Never Confuse a High Win Rate With an Edge

Expectancy matters more than percentage of winning trades.

## 5. Data Decides

If forward testing demonstrates that the hypothesis is wrong:

**Abandon or substantially modify the strategy.**

The objective is not to prove the original idea correct.

The objective is to discover whether a repeatable market inefficiency actually exists.

---

# 64. Long-Term Goal

The final system should operate as an automated IPO failure engine capable of:

**Discovering IPOs**

→ **Collecting offering/fundamental data**

→ **Scoring them**

→ **Watching aftermarket behavior**

→ **Identifying failure**

→ **Calculating risk**

→ **Checking borrow/options**

→ **Generating trades**

→ **Managing positions**

→ **Recording results**

→ **Learning from the accumulated dataset**

The desired end product is not:

> "Short IPOs."

It is:

# **Identify newly public companies where the probability and magnitude of failure create a favorable asymmetric trading opportunity while strictly controlling the possibility of catastrophic short-side loss.**

---

## Current Status

**System:** IPO Failure Short System
**Version:** 0.1
**Environment:** Sandbox / Paper Trading
**Starting Equity:** $500
**Maximum Gross Exposure:** $1,000
**Live Capital:** $0
**Forward Test:** Active
**Next Milestone:** Complete initial 10-trading-day prospective test and analyze Version 0.1 results.
