# The Investor — Strategy Documentation
*Last updated: 2026-03-02*

## Primary Strategy: Insider + Congressional Following
Trade based on SEC Form 4 insider PURCHASES and Congressional stock trades. Two alpha sources, one portfolio.

### Corporate Insider Signal Hierarchy (highest to lowest priority)
1. **Cluster buys** — multiple insiders buying same stock within days
2. **CEO/CFO purchases >$250K** — highest conviction
3. **Director/Officer purchases >$50K** — strong signal
4. **Insider buy after price drop** — contrarian + insider confidence

### Corporate Insider Filters
- ✅ Open-market purchases (transaction code "P")
- ❌ Grants (A), exercises (M), gifts (G), sales (S)
- ❌ Automatic/planned purchases (Rule 10b5-1)

### Congressional Trade Signal Hierarchy
1. **Any purchase >$100K** — significant conviction
2. **Committee-relevant buys** — senator on Banking Committee buying bank stocks (the real alpha)
3. **Cluster buys** — multiple Congress members buying same stock
4. **Speaker/Chair purchases** — leadership has the most inside info

### Congressional Trade Filters
- ✅ Purchases only (not sales, unless massive)
- ✅ Individual stock picks (not index funds/ETFs)
- Data sources: Senate/House financial disclosure portals, Quiver Quantitative, Capitol Trades

## Cash Management
- **Zero idle cash** — deploy everything, always
- Priority: insider signals → congressional signals → winning positions → sector conviction picks
- **⚠️ HARD RULE: NEVER USE MARGIN. Alpaca defaults to margin (4x). ONLY use the `cash` field from /v2/account, NEVER `buying_power`. If cash < $0, IMMEDIATELY sell worst performer before doing ANYTHING else. This is non-negotiable.**
- Before ANY buy order: verify `cash` (not buying_power) >= order cost + $500 buffer
- **MINIMUM CASH FLOOR: $500.** Never let cash drop below $500. If cash < $500 after a trade, you've over-deployed.
- If cash goes negative for any reason: emergency sell until cash > $500
- The "zero idle cash" rule means deploy down to $500, NOT to $0
- No cash reserve needed
- Threshold: $1 minimum (deploy every dollar)

## Risk Rules
- **No margin** — cash only, never buying power
- **Stop loss: -8%** — auto-sell if position drops 8%
- **Take profit: +15%** — sell half when position hits +15%
- **No single position >15% of portfolio**

## Quiet Market Rules (No New Insider Signals)

### 1. Tighten Stops on Aging Positions
- If a position is **7+ days old** with NO new insider activity for that ticker AND is in the red → tighten stop from -8% to **-5%**
- Stale conviction = less rope
- Reset timer if new insider buy appears for that ticker

### 2. Winner Rotation
- If no new signals for **3+ consecutive trading days** → add to top 3 performing positions (ones with strongest insider backing)
- Sell bottom performer to fund the rotation
- Only rotate if bottom performer has no recent insider activity (14 days)

### 3. Trim Dead Weight
- Any position **flat (±1%) for 10+ trading days** with no new insider buys → sell half
- Redeploy proceeds to winners or hold for next signal
- Exception: positions with cluster buy signals in last 30 days get more time

### 4. Sector Momentum Shift
- Weekly review (Monday morning): check which sectors have the most insider cluster activity in last 30 days
- If current portfolio is overweight in sectors with ZERO recent insider activity → trim those positions by 25%
- Reallocate into sectors showing fresh insider clusters
- Use sector ETFs (XLE, XLF, XLK, etc.) as temporary parking if no specific stock signal

## Options Rules
- Max 10% of portfolio value
- Buy only (calls/puts), no selling/writing
- 2-6 week expiry
- +50% take profit, -40% stop loss

## Schedule
| Job | Time | Model | Channel |
|-----|------|-------|---------|
| Morning Briefing | 9:45 AM M-F | Opus | #investor-briefing |
| Monitor | Every 15min 9-3:45 M-F | Sonnet | #investor-plays (trades only) |
| Price Update | Every 15min 9-4 M-F | Sonnet | GitHub push |
| Closing Bell | 4:05 PM M-F | Sonnet | #investor-briefing |

## Channel Rules (STRICT)
- **#investor-plays** = Trade alerts ONLY (🟢 BUY / 🔴 SELL with price + thesis)
- **#investor-briefing** = Morning + closing bell briefings only
- **NEVER** mix status updates, API errors, or commentary into #investor-plays

## Data Pipeline
1. `edgar-quick.py` → `edgar-data.json` (SEC Form 4 + 8-K events)
2. `alpaca.js` → `alpaca-data.json` (positions, orders, account)
3. `update-prices.js` → `picks.json` → GitHub Pages
4. `deployment-tracker.json` — tracks daily cash deployment state

## Portfolio State (EOD 2/27)
- Value: $99,156
- Positions: 16
- Cash: $843
- P&L: -$844 (-0.84%)
- Day 2 of paper trading

## Key Decisions Log
- 2/26: Started paper trading with $100K
- 2/26: Switched from general picking to insider following strategy
- 2/27: Fixed margin issue (negative cash from unsettled trades)
- 2/27: Lowered insider threshold from $100K to $50K
- 2/27: Implemented zero idle cash rule
- 2/27: GS stopped out at -8.5% (first stop loss trigger)
- 2/27: DELL profit-taken multiple times at +15-18%
