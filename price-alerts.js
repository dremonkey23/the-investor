// Price Alert Pipeline — runs every 15 min via cron
// Pings Discord when any Investor pick moves ±10% from entry
// Zero AI cost — pure code

const fs = require('fs');
const path = require('path');

const PICKS_FILE = path.join(__dirname, 'picks.json');
const ALERTS_STATE = path.join(__dirname, 'alerts-state.json');
const THRESHOLD = 0.10; // 10% move triggers alert

async function fetchJSON(url) {
  const res = await fetch(url, { headers: { 'User-Agent': 'TheInvestor/1.0' } });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function getStockPrice(ticker) {
  try {
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(ticker)}?interval=1d&range=1d`;
    const data = await fetchJSON(url);
    return data.chart?.result?.[0]?.meta?.regularMarketPrice || null;
  } catch { return null; }
}

async function getCryptoPrice(query) {
  try {
    if (query && query.length > 20) {
      const data = await fetchJSON(`https://api.dexscreener.com/latest/dex/tokens/${query}`);
      if (data.pairs?.length) return parseFloat(data.pairs[0].priceUsd);
    }
    const data = await fetchJSON(`https://api.dexscreener.com/latest/dex/search?q=${encodeURIComponent(query)}`);
    const sol = (data.pairs || []).find(p => p.chainId === 'solana');
    return sol ? parseFloat(sol.priceUsd) : null;
  } catch { return null; }
}

// Load alert state (tracks which alerts we already sent to avoid spam)
function loadAlertState() {
  try { return JSON.parse(fs.readFileSync(ALERTS_STATE, 'utf8')); }
  catch { return {}; }
}

function saveAlertState(state) {
  fs.writeFileSync(ALERTS_STATE, JSON.stringify(state, null, 2));
}

async function main() {
  let data;
  try { data = JSON.parse(fs.readFileSync(PICKS_FILE, 'utf8')); }
  catch { console.log('No picks.json'); process.exit(0); }

  const stocks = data.stocks || [];
  const crypto = data.crypto || [];
  const all = [...stocks.map(p => ({ ...p, asset: 'stock' })), ...crypto.map(p => ({ ...p, asset: 'crypto' }))];

  if (!all.length) { console.log('No picks to monitor.'); process.exit(0); }

  const state = loadAlertState();
  const alerts = [];
  const now = Date.now();

  for (const pick of all) {
    if (pick.status === 'closed' || !pick.entryPrice) continue;

    const key = pick.ticker || pick.token || pick.contract;
    if (!key) continue;

    // Get current price
    let price;
    if (pick.asset === 'stock') {
      price = await getStockPrice(pick.ticker);
    } else {
      price = await getCryptoPrice(pick.contract || pick.token || pick.ticker);
    }

    if (!price) continue;

    const pctChange = (price - pick.entryPrice) / pick.entryPrice;
    const absPct = Math.abs(pctChange);

    // Check if ±10% threshold crossed
    if (absPct >= THRESHOLD) {
      // Check if we already alerted at this threshold level (avoid spam)
      // Re-alert if it crosses a new 10% band (e.g., 10%, 20%, 30%)
      const band = Math.floor(absPct / THRESHOLD) * 10;
      const stateKey = `${key}_${band}`;
      
      if (!state[stateKey] || (now - state[stateKey]) > 6 * 60 * 60 * 1000) { // re-alert after 6 hours
        const direction = pctChange > 0 ? '📈' : '🚨';
        const action = pctChange > 0 ? 'take profit?' : 'revisit or hold?';
        const name = pick.ticker || pick.token;
        const pctStr = (pctChange >= 0 ? '+' : '') + (pctChange * 100).toFixed(1) + '%';
        const entryStr = pick.entryPrice < 0.01 ? '$' + pick.entryPrice.toPrecision(3) : '$' + pick.entryPrice.toFixed(2);
        const currentStr = price < 0.01 ? '$' + price.toPrecision(3) : '$' + price.toFixed(2);

        alerts.push(`${direction} **${name}** ${pctStr} (${entryStr} → ${currentStr}) — ${action}`);
        state[stateKey] = now;
      }
    }

    // Rate limit
    await new Promise(r => setTimeout(r, 400));
  }

  saveAlertState(state);

  if (alerts.length === 0) {
    console.log('No alerts triggered.');
    process.exit(0);
  }

  // Output alerts for the cron agent to post
  console.log('ALERTS:');
  alerts.forEach(a => console.log(a));
  
  // Exit code 2 = alerts to post
  process.exit(2);
}

main().catch(e => { console.error(e); process.exit(1); });
