// Alpaca API helper for The Investor
// Fetches account, positions, orders, and trade history
// Output: investor/alpaca-data.json (consumed by index.html)

const https = require('https');
const fs = require('fs');
const path = require('path');

const API_KEY = 'PK5BLOFWV3NILHF75FSG4NQPKY';
const API_SECRET = '2NR9EKz7JEgPCHn2wP5rdM8NPn4VRBF8JdUMMsduX1Lg';
const BASE = 'paper-api.alpaca.markets';

function apiGet(endpoint) {
  return new Promise((resolve, reject) => {
    const opts = {
      hostname: BASE,
      path: `/v2${endpoint}`,
      headers: { 'APCA-API-KEY-ID': API_KEY, 'APCA-API-SECRET-KEY': API_SECRET }
    };
    https.get(opts, res => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch (e) { reject(new Error(`Parse error on ${endpoint}: ${data.slice(0, 200)}`)); }
      });
    }).on('error', reject);
  });
}

async function main() {
  try {
    const [account, positions, orders, activities] = await Promise.all([
      apiGet('/account'),
      apiGet('/positions'),
      apiGet('/orders?status=all&limit=100&direction=desc'),
      apiGet('/account/activities/FILL?direction=desc&page_size=100')
    ]);

    const output = {
      account: {
        portfolioValue: parseFloat(account.portfolio_value),
        cash: parseFloat(account.cash),
        buyingPower: parseFloat(account.buying_power),
        equity: parseFloat(account.equity),
        longMarketValue: parseFloat(account.long_market_value),
        shortMarketValue: parseFloat(account.short_market_value),
        pnl: parseFloat(account.equity) - 100000, // starting capital
        pnlPct: ((parseFloat(account.equity) - 100000) / 100000 * 100)
      },
      positions: positions.map(p => ({
        symbol: p.symbol,
        qty: parseFloat(p.qty),
        side: p.side,
        avgEntry: parseFloat(p.avg_entry_price),
        currentPrice: parseFloat(p.current_price),
        marketValue: parseFloat(p.market_value),
        unrealizedPnl: parseFloat(p.unrealized_pl),
        unrealizedPnlPct: parseFloat(p.unrealized_plpc) * 100,
        change: parseFloat(p.change_today) * 100
      })),
      orders: orders.slice(0, 50).map(o => ({
        id: o.id,
        symbol: o.symbol,
        side: o.side,
        qty: parseFloat(o.qty || o.notional || 0),
        type: o.type,
        status: o.status,
        filledQty: parseFloat(o.filled_qty || 0),
        filledAvgPrice: parseFloat(o.filled_avg_price || 0),
        submittedAt: o.submitted_at,
        filledAt: o.filled_at
      })),
      history: activities.map(a => ({
        action: a.side === 'buy' ? 'BUY' : 'SELL',
        ticker: a.symbol,
        qty: parseFloat(a.qty),
        price: parseFloat(a.price),
        date: a.transaction_time ? a.transaction_time.split('T')[0] : '',
        time: a.transaction_time,
        orderId: a.order_id
      })),
      metadata: {
        lastUpdated: new Date().toISOString(),
        startingCapital: 100000
      }
    };

    // Calculate win rate from closed positions (filled sells)
    const sells = output.history.filter(h => h.action === 'SELL');
    // We'll compute win rate from positions with realized P&L later

    const outPath = path.join(__dirname, 'alpaca-data.json');
    fs.writeFileSync(outPath, JSON.stringify(output, null, 2));
    console.log(`Updated alpaca-data.json: $${output.account.portfolioValue} portfolio, ${output.positions.length} positions, ${output.history.length} trades`);
  } catch (e) {
    console.error('Alpaca fetch error:', e.message);
    process.exit(1);
  }
}

main();
