"""
SEC EDGAR Scraper
Scrapes insider trades (Form 4), and material events (8-K) using EDGAR EFTS API.
Parses actual Form 4 XML filings for transaction details.
"""

import json
import logging
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

OUTPUT = Path(__file__).parent / "edgar-data.json"

HEADERS = {
    "User-Agent": "Mirzayan LLC andre@mirzayanconsulting.com",
    "Accept": "application/json",
}
EDGAR_BASE = "https://www.sec.gov/Archives/edgar/data"
EFTS_URL = "https://efts.sec.gov/LATEST/search-index"


def efts_search(forms: str, days_back: int = 3, size: int = 40) -> list:
    """Search EDGAR EFTS for recent filings of a given form type."""
    today = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    params = {
        "forms": forms,
        "dateRange": "custom",
        "startdt": start,
        "enddt": today,
        "from": 0,
        "size": size,
    }

    url = f"{EFTS_URL}?{urlencode(params)}"
    try:
        with httpx.Client(timeout=10, headers=HEADERS) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                hits = data.get("hits", {}).get("hits", [])
                total = data.get("hits", {}).get("total", {}).get("value", 0)
                log.info(f"  EFTS: {len(hits)} hits (total: {total}) for form {forms}")
                return hits
            else:
                log.error(f"  EFTS returned {resp.status_code}")
    except Exception as e:
        log.error(f"  EFTS error: {e}")

    return []


def build_filing_xml_url(adsh: str, cik: str, filename: str) -> str:
    """Build URL to a specific filing document on EDGAR."""
    # adsh format: 0001234567-26-000001 -> 000123456726000001
    adsh_clean = adsh.replace("-", "")
    return f"{EDGAR_BASE}/{cik.lstrip('0')}/{adsh_clean}/{filename}"


def fetch_form4_xml(adsh: str, display_names: list, ciks: list) -> dict:
    """Fetch and parse a Form 4 XML filing."""
    time.sleep(0.5)  # SEC rate limit

    # Build the index page URL to find the XML file
    adsh_clean = adsh.replace("-", "")
    # Use the second CIK (usually the company, first is the insider)
    cik = ciks[1] if len(ciks) > 1 else ciks[0]
    cik_num = cik.lstrip("0")

    index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_num}/{adsh_clean}/"

    try:
        with httpx.Client(timeout=10, headers=HEADERS) as client:
            # Try to get the index page to find the XML file
            resp = client.get(index_url)
            if resp.status_code != 200:
                log.warning(f"  Index page {resp.status_code} for {adsh}")
                return {}

            # Find XML files in the index
            text = resp.text
            import re
            # Look for .xml files that aren't R files or primary_doc
            xml_files = re.findall(r'href="([^"]+\.xml)"', text)
            # Prefer files with form4, xslF345, or the main doc
            target_xml = None
            for f in xml_files:
                fname = f.split("/")[-1]
                if "R" not in fname and fname != "primary_doc.xml":
                    target_xml = fname
                    break
            if not target_xml and xml_files:
                target_xml = xml_files[0].split("/")[-1]

            if not target_xml:
                return {}

            # Fetch the XML
            xml_url = f"{index_url}{target_xml}"
            time.sleep(0.5)
            resp2 = client.get(xml_url)
            if resp2.status_code != 200:
                return {}

            return parse_form4_xml(resp2.text, xml_url)

    except Exception as e:
        log.error(f"  Error fetching Form 4 XML {adsh}: {e}")
        return {}


def parse_form4_xml(xml_text: str, url: str) -> dict:
    """Parse Form 4 XML into structured trade data."""
    result = {"url": url}

    try:
        # Handle namespace issues
        xml_text = xml_text.replace('xmlns="http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=', 'xmlns_removed="')
        root = ET.fromstring(xml_text)

        # Remove namespace prefixes for easier parsing
        for elem in root.iter():
            if "}" in elem.tag:
                elem.tag = elem.tag.split("}", 1)[1]

        # Issuer info
        issuer = root.find(".//issuer")
        if issuer is not None:
            result["company"] = issuer.findtext("issuerName", "").strip()
            result["ticker"] = issuer.findtext("issuerTradingSymbol", "").strip()

        # Reporting person (insider)
        owner = root.find(".//reportingOwner")
        if owner is not None:
            oid = owner.find("reportingOwnerId")
            if oid is not None:
                result["insiderName"] = oid.findtext("rptOwnerName", "").strip()
            rel = owner.find("reportingOwnerRelationship")
            if rel is not None:
                title = rel.findtext("officerTitle", "").strip()
                if not title:
                    if rel.findtext("isDirector", "") == "1" or rel.findtext("isDirector", "") == "true":
                        title = "Director"
                    elif rel.findtext("isTenPercentOwner", "") == "1":
                        title = "10% Owner"
                    elif rel.findtext("isOfficer", "") == "1":
                        title = "Officer"
                result["insiderTitle"] = title

        # Non-derivative transactions
        total_shares = 0
        total_value = 0.0
        price = 0.0
        txn_type = ""
        txn_date = ""

        for txn in root.findall(".//nonDerivativeTransaction"):
            amounts = txn.find("transactionAmounts")
            if amounts is not None:
                shares_str = amounts.findtext("transactionShares/value", "0") or "0"
                px_str = amounts.findtext("transactionPricePerShare/value", "0") or "0"

                try:
                    shares = float(shares_str)
                except ValueError:
                    shares = 0
                try:
                    px = float(px_str)
                except ValueError:
                    px = 0

                total_shares += shares
                if px > 0:
                    price = px
                    total_value += shares * px

            coding = txn.find("transactionCoding")
            if coding is not None:
                code = coding.findtext("transactionCode", "")
                if code == "P":
                    txn_type = "Purchase"
                elif code == "S":
                    txn_type = "Sale"
                elif code == "A":
                    txn_type = "Grant"
                elif code == "M":
                    txn_type = "Exercise"
                elif code == "G":
                    txn_type = "Gift"

            date_el = txn.find("transactionDate")
            if date_el is not None:
                txn_date = date_el.findtext("value", "")

        # Post-transaction holdings
        holdings_after = 0
        for h in root.findall(".//postTransactionAmounts"):
            val = h.findtext("sharesOwnedFollowingTransaction/value", "0")
            try:
                holdings_after = max(holdings_after, int(float(val or "0")))
            except ValueError:
                pass

        result["transactionType"] = txn_type
        result["shares"] = int(total_shares)
        result["pricePerShare"] = round(price, 2)
        result["totalValue"] = round(total_value, 2)
        result["date"] = txn_date
        result["holdingsAfter"] = holdings_after
        result["isNotable"] = txn_type == "Purchase" and total_value > 100000

    except ET.ParseError as e:
        log.error(f"  XML parse error: {e}")
    except Exception as e:
        log.error(f"  Error parsing Form 4: {e}")

    return result


def scrape_form4_filings() -> list:
    """Scrape recent Form 4 insider trading filings via EFTS API."""
    log.info("Scraping Form 4 insider trading filings...")
    trades = []

    hits = efts_search("4", days_back=3, size=20)

    for hit in hits:
        src = hit.get("_source", {})
        adsh = src.get("adsh", "")
        ciks = src.get("ciks", [])
        names = src.get("display_names", [])

        if not adsh or not ciks:
            continue

        # Quick info from EFTS (before fetching XML)
        company_name = ""
        insider_name = ""
        for name in names:
            if "(CIK" in name:
                clean = name.split("(CIK")[0].strip()
                if not insider_name:
                    insider_name = clean
                else:
                    company_name = clean

        log.info(f"  Processing: {insider_name} -> {company_name} ({adsh})")

        # Fetch and parse the actual XML
        detail = fetch_form4_xml(adsh, names, ciks)

        if detail and detail.get("company"):
            trade = {
                "company": detail.get("company", company_name),
                "ticker": detail.get("ticker", ""),
                "insiderName": detail.get("insiderName", insider_name),
                "insiderTitle": detail.get("insiderTitle", ""),
                "transactionType": detail.get("transactionType", ""),
                "shares": detail.get("shares", 0),
                "pricePerShare": detail.get("pricePerShare", 0),
                "totalValue": detail.get("totalValue", 0),
                "date": detail.get("date", src.get("period_ending", "")),
                "holdingsAfter": detail.get("holdingsAfter", 0),
                "isNotable": detail.get("isNotable", False),
                "url": detail.get("url", ""),
            }
            trades.append(trade)
        else:
            # Use EFTS metadata as fallback
            trades.append({
                "company": company_name,
                "ticker": "",
                "insiderName": insider_name,
                "insiderTitle": "",
                "transactionType": "",
                "shares": 0,
                "pricePerShare": 0,
                "totalValue": 0,
                "date": src.get("period_ending", ""),
                "holdingsAfter": 0,
                "isNotable": False,
                "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ciks[0]}&type=4&dateb=&owner=include&count=10",
            })

    return trades


def scrape_8k_filings() -> list:
    """Scrape recent 8-K material event filings via EFTS API."""
    log.info("Scraping 8-K material event filings...")
    events = []

    hits = efts_search("8-K", days_back=3, size=20)

    for hit in hits:
        src = hit.get("_source", {})
        names = src.get("display_names", [])
        ciks = src.get("ciks", [])
        items = src.get("items", [])
        adsh = src.get("adsh", "")

        company = ""
        for name in names:
            if "(CIK" in name:
                company = name.split("(CIK")[0].strip()
                break

        # Map 8-K item codes to human-readable types
        item_map = {
            "1.01": "Entry into Material Agreement",
            "1.02": "Termination of Material Agreement",
            "2.01": "Completion of Acquisition/Disposition",
            "2.02": "Results of Operations (Earnings)",
            "2.05": "Costs Associated with Exit Activities",
            "2.06": "Material Impairments",
            "3.01": "Delisting/Transfer Failure",
            "5.02": "Departure/Election of Directors/Officers",
            "5.03": "Amendments to Articles/Bylaws",
            "5.07": "Submission of Matters to Vote",
            "7.01": "Regulation FD Disclosure",
            "8.01": "Other Events",
            "9.01": "Financial Statements and Exhibits",
        }

        event_types = [item_map.get(i, i) for i in items if i in item_map]
        event_type = "; ".join(event_types) if event_types else "; ".join(items) if items else "8-K Filing"

        # Build URL
        adsh_clean = adsh.replace("-", "")
        cik_num = ciks[0].lstrip("0") if ciks else ""
        filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik_num}/{adsh_clean}/" if cik_num else ""

        events.append({
            "company": company,
            "ticker": "",
            "eventType": event_type,
            "date": src.get("file_date", ""),
            "summary": f"Items: {', '.join(items)}" if items else "",
            "url": filing_url,
        })

    return events


def main():
    log.info("=" * 60)
    log.info("SEC EDGAR Scraper")
    log.info("Insider Trades (Form 4) | Material Events (8-K)")
    log.info("=" * 60)

    try:
        insider_trades = scrape_form4_filings()
    except Exception as e:
        log.error(f"Form 4 scraping failed: {e}")
        insider_trades = []
    log.info(f"Total insider trades: {len(insider_trades)}")
    notable = [t for t in insider_trades if t.get("isNotable")]
    if notable:
        log.info(f"🔥 Notable insider buys (>$100K): {len(notable)}")
        for t in notable:
            log.info(f"   {t['insiderName']} bought ${t['totalValue']:,.0f} of {t['ticker']} ({t['company']})")

    try:
        material_events = scrape_8k_filings()
    except Exception as e:
        log.error(f"8-K scraping failed: {e}")
        material_events = []
    log.info(f"Total material events: {len(material_events)}")

    # Always save output
    output = {
        "scrapedAt": datetime.now().isoformat(),
        "insiderTrades": insider_trades,
        "materialEvents": material_events,
    }

    OUTPUT.write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")
    log.info(f"Results saved to {OUTPUT}")
    log.info("Done!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error(f"Fatal: {e}")
        import traceback
        traceback.print_exc()
