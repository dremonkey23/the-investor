// Price updater — runs every hour via cron, zero AI tokens
// Fetches live prices for stock + crypto picks, updates P&L, pushes to GitHub

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const PICKS_FILE = path.join(__dirname, 'picks.json');

async function fetchJSON(url) {
  const res = await fetch(url, { headers: { 'User-Agent': 'TheInvestor/1.0' } });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// Yahoo Finance — free, no key needed
async function getStockPrice(ticker) {
  try {
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(ticker)}?interval=1d&range=1d`;
    const data = await fetchJSON(url);
    const meta = data.chart?.result?.[0]?.meta;
    return meta?.regularMarketPrice || null;
  } catch (e) {
    console.log(`  [WARN] Could not fetch ${ticker}: ${e.message}`);
    return null;
  }
}

// DexScreener — free, no key needed
async function getCryptoPrice(tokenOrContract) {
  try {
    // Try by contract address first
    if (tokenOrContract && tokenOrContract.length > 20) {
      const url = `https://api.dexscreener.com/latest/dex/tokens/${tokenOrContract}`;
      const data = await fetchJSON(url);
      if (data.pairs && data.pairs.length > 0) {
        return { price: parseFloat(data.pairs[0].priceUsd), mcap: data.pairs[0].marketCap || null };
      }
    }
    // Fallback: search by name
    const url = `https://api.dexscreener.com/latest/dex/search?q=${encodeURIComponent(tokenOrContract)}`;
    const data = await fetchJSON(url);
    const solPair = (data.pairs || []).find(p => p.chainId === 'solana');
    if (solPair) {
      return { price: parseFloat(solPair.priceUsd), mcap: solPair.marketCap || null };
    }
    return null;
  } catch (e) {
    console.log(`  [WARN] Could not fetch crypto ${tokenOrContract}: ${e.message}`);
    return null;
  }
}

async function main() {
  const ts = new Date().toISOString();
  console.log(`[${ts}] Updating prices...`);

  let data;
  try {
    data = JSON.parse(fs.readFileSync(PICKS_FILE, 'utf8'));
  } catch (e) {
    console.log('No picks.json found, nothing to update.');
    process.exit(0);
  }

  const stocks = data.stocks || [];
  const crypto = data.crypto || [];
  let updated = false;

  // Update stock prices
  for (const pick of stocks) {
    if (!pick.ticker || pick.status === 'closed') continue;
    const price = await getStockPrice(pick.ticker);
    if (price !== null) {
      pick.currentPrice = price;
      if (pick.entryPrice) {
        pick.pnl = ((price - pick.entryPrice) / pick.entryPrice) * 100;
      }
      updated = true;
      console.log(`  ${pick.ticker}: $${pick.entryPrice?.toFixed(2)} → $${price.toFixed(2)} (${pick.pnl >= 0 ? '+' : ''}${pick.pnl?.toFixed(1)}%)`);
    }
    // Rate limit — be nice to Yahoo
    await new Promise(r => setTimeout(r, 500));
  }

  // Update crypto prices
  for (const pick of crypto) {
    if (pick.status === 'closed') continue;
    const query = pick.contract || pick.token || pick.ticker;
    if (!query) continue;
    const result = await getCryptoPrice(query);
    if (result) {
      pick.currentPrice = result.price;
      if (result.mcap) pick.mcap = result.mcap;
      if (pick.entryPrice) {
        pick.pnl = ((result.price - pick.entryPrice) / pick.entryPrice) * 100;
      }
      updated = true;
      const pStr = result.price < 0.01 ? '$' + result.price.toPrecision(3) : '$' + result.price.toFixed(4);
      console.log(`  ${pick.token || pick.ticker}: ${pStr} (${pick.pnl >= 0 ? '+' : ''}${pick.pnl?.toFixed(1)}%)`);
    }
    await new Promise(r => setTimeout(r, 500));
  }

  if (!updated) {
    console.log('No prices updated (no active picks or all APIs failed).');
    process.exit(0);
  }

  // Save
  data.metadata = data.metadata || {};
  data.metadata.lastUpdated = ts;
  fs.writeFileSync(PICKS_FILE, JSON.stringify(data, null, 2));
  console.log('picks.json updated.');

  // Push to GitHub
  try {
    execSync('git add picks.json', { cwd: __dirname, stdio: 'pipe' });
    execSync(`git commit -m "Price update ${new Date().toISOString().slice(0, 16)}"`, { cwd: __dirname, stdio: 'pipe' });
    execSync('git push origin main', { cwd: __dirname, stdio: 'pipe' });
    console.log('Pushed to GitHub ✅');
  } catch (e) {
    // Nothing to commit is fine
    if (e.message.includes('nothing to commit')) {
      console.log('No changes to push.');
    } else {
      console.log('Git push failed:', e.message);
    }
  }

  console.log('Done.');
}

main().catch(e => { console.error(e); process.exit(1); });
