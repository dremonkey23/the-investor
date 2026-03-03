"""Quick EDGAR scraper - fast version using EFTS API + full-text search."""
import json, time, re, xml.etree.ElementTree as ET
import httpx
from datetime import datetime, timedelta
from pathlib import Path

HEADERS = {"User-Agent": "Mirzayan LLC andre@mirzayanconsulting.com", "Accept": "application/json"}
OUTPUT = Path(__file__).parent / "edgar-data.json"

today = datetime.now().strftime("%Y-%m-%d")
start = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")

trades = []
events = []

# Form 4 filings
print(f"Scanning Form 4 filings from {start} to {today}...")
with httpx.Client(timeout=15, headers=HEADERS) as c:
    url = f"https://efts.sec.gov/LATEST/search-index?forms=4&dateRange=custom&startdt={start}&enddt={today}&from=0&size=40"
    r = c.get(url)
    hits = r.json().get("hits", {}).get("hits", []) if r.status_code == 200 else []
    print(f"Found {len(hits)} Form 4 filings")

    for i, hit in enumerate(hits):
        src = hit.get("_source", {})
        adsh = src.get("adsh", "")
        ciks = src.get("ciks", [])
        names = src.get("display_names", [])
        filing_date = src.get("file_date", src.get("period_ending", ""))

        insider, company = "", ""
        for n in names:
            if "(CIK" in n:
                clean = n.split("(CIK")[0].strip()
                if not insider:
                    insider = clean
                else:
                    company = clean

        cik = ciks[1] if len(ciks) > 1 else (ciks[0] if ciks else "")
        cik_num = cik.lstrip("0")
        adsh_clean = adsh.replace("-", "")
        filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik_num}/{adsh_clean}/"

        # Try to get the XML for transaction details
        ticker, txn_type = "", ""
        shares, price, total_val = 0, 0.0, 0.0
        txn_date = src.get("period_ending", "")
        notable = False

        try:
            # Get filing index to find XML
            idx = c.get(filing_url, timeout=8)
            if idx.status_code == 200:
                xml_files = re.findall(r'href="([^"]+\.xml)"', idx.text)
                target = None
                for f in xml_files:
                    fn = f.split("/")[-1]
                    if "R" not in fn and fn != "primary_doc.xml":
                        target = fn
                        break
                if not target and xml_files:
                    target = xml_files[0].split("/")[-1]

                if target:
                    time.sleep(0.2)
                    xr = c.get(f"{filing_url}{target}", timeout=8)
                    if xr.status_code == 200:
                        try:
                            root = ET.fromstring(xr.text)
                            for elem in root.iter():
                                if "}" in elem.tag:
                                    elem.tag = elem.tag.split("}", 1)[1]

                            iss = root.find(".//issuer")
                            if iss is not None:
                                ticker = (iss.findtext("issuerTradingSymbol", "") or "").strip()
                                company = (iss.findtext("issuerName", "") or company).strip()

                            for txn in root.findall(".//nonDerivativeTransaction"):
                                amt = txn.find("transactionAmounts")
                                if amt is not None:
                                    s = float(amt.findtext("transactionShares/value", "0") or "0")
                                    p2 = float(amt.findtext("transactionPricePerShare/value", "0") or "0")
                                    shares += s
                                    if p2 > 0:
                                        price = p2
                                        total_val += s * p2
                                cod = txn.find("transactionCoding")
                                if cod is not None:
                                    code = cod.findtext("transactionCode", "")
                                    txn_type = {"P": "Purchase", "S": "Sale", "A": "Grant", "M": "Exercise", "G": "Gift", "F": "Tax"}.get(code, code)
                                d = txn.find("transactionDate")
                                if d is not None:
                                    txn_date = d.findtext("value", "") or txn_date

                            notable = txn_type == "Purchase" and total_val > 50000
                        except Exception as e:
                            print(f"  XML parse error: {e}")
        except httpx.TimeoutException:
            print(f"  Timeout on filing {i+1}")
        except Exception as e:
            print(f"  Error on filing {i+1}: {e}")

        trades.append({
            "company": company, "ticker": ticker, "insiderName": insider,
            "transactionType": txn_type, "shares": int(shares),
            "pricePerShare": round(price, 2), "totalValue": round(total_val, 2),
            "date": txn_date, "filingDate": filing_date,
            "isNotable": notable, "url": filing_url,
        })
        tag = " *** NOTABLE ***" if notable else ""
        print(f"  [{i+1}/{len(hits)}] {insider} -> {ticker or company} {txn_type} ${total_val:,.0f}{tag}")
        time.sleep(0.3)

# 8-K material events
print(f"\nScanning 8-K filings...")
url8k = f"https://efts.sec.gov/LATEST/search-index?forms=8-K&dateRange=custom&startdt={start}&enddt={today}&from=0&size=15"
r8 = httpx.get(url8k, headers=HEADERS, timeout=10)
hits8 = r8.json().get("hits", {}).get("hits", []) if r8.status_code == 200 else []
print(f"Found {len(hits8)} 8-K filings")
for h in hits8:
    src = h.get("_source", {})
    names = src.get("display_names", [])
    co = names[0].split("(CIK")[0].strip() if names else ""
    items = src.get("items", [])
    events.append({"company": co, "eventType": "; ".join(items), "date": src.get("file_date", "")})

# Save
output = {"scrapedAt": datetime.now().isoformat(), "insiderTrades": trades, "materialEvents": events}
OUTPUT.write_text(json.dumps(output, indent=2, default=str))

notable_list = [t for t in trades if t["isNotable"]]
purchases = [t for t in trades if t["transactionType"] == "Purchase"]
print(f"\n=== SUMMARY ===")
print(f"Total filings: {len(trades)}")
print(f"Purchases: {len(purchases)}")
print(f"Notable buys (>$50K): {len(notable_list)}")
if notable_list:
    print(f"\nNOTABLE INSIDER PURCHASES:")
    for t in notable_list:
        print(f"  {t['insiderName']} bought ${t['totalValue']:,.0f} of {t['ticker']} on {t['date']}")
print("\nDone!")
