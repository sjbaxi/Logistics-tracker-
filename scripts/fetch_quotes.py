#!/usr/bin/env python3
"""
Fetches live quotes for a curated list of NSE-listed logistics companies
and writes them to data.json at the repo root.

This script is run on a schedule by .github/workflows/update-quotes.yml —
it has no knowledge of whether anyone is looking at the site.
"""
import json
import sys
import urllib.request
from datetime import datetime, timezone

COMPANIES = [
    {"symbol": "CONCOR",     "name": "Container Corp. of India", "segment": "Rail / Container"},
    {"symbol": "DELHIVERY",  "name": "Delhivery Ltd",             "segment": "E-commerce / 3PL"},
    {"symbol": "BLUEDART",   "name": "Blue Dart Express",         "segment": "Air / Express"},
    {"symbol": "TCIEXP",     "name": "TCI Express",               "segment": "Surface Express"},
    {"symbol": "TCI",        "name": "Transport Corp. of India",  "segment": "Multimodal"},
    {"symbol": "MAHLOG",     "name": "Mahindra Logistics",        "segment": "3PL / Supply Chain"},
    {"symbol": "VRLLOG",     "name": "VRL Logistics",             "segment": "Surface Freight"},
    {"symbol": "ALLCARGO",   "name": "Allcargo Logistics",        "segment": "Freight Forwarding"},
    {"symbol": "AEGISLOG",   "name": "Aegis Logistics",           "segment": "LPG / Liquid Terminals"},
    {"symbol": "GESHIP",     "name": "Great Eastern Shipping",    "segment": "Shipping"},
    {"symbol": "SCI",        "name": "Shipping Corp. of India",   "segment": "Shipping"},
    {"symbol": "SNOWMAN",    "name": "Snowman Logistics",         "segment": "Cold Chain"},
    {"symbol": "NAVKARCORP", "name": "Navkar Corporation",        "segment": "ICD / Container"},
    {"symbol": "TVSSCS",     "name": "TVS Supply Chain Solutions","segment": "3PL / Supply Chain"},
    {"symbol": "SICAL",      "name": "Sical Logistics",           "segment": "Ports / Multimodal"},
    {"symbol": "GATI",       "name": "Gati Ltd",                  "segment": "Express / Distribution"},
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; nse-logistics-index/1.0)"}


def fetch_quote(symbol: str):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS?interval=1d&range=1d"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as resp:
        payload = json.loads(resp.read().decode())
    meta = payload["chart"]["result"][0]["meta"]
    price = meta.get("regularMarketPrice")
    prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")
    if price is None:
        raise ValueError("no price in response")
    change_pct = None
    if prev_close:
        change_pct = round((price - prev_close) / prev_close * 100, 2)
    return {"price": price, "prevClose": prev_close, "changePct": change_pct}


def main():
    rows = []
    failures = 0
    for company in COMPANIES:
        row = dict(company)
        try:
            row.update(fetch_quote(company["symbol"]))
            row["status"] = "ok"
        except Exception as exc:  # noqa: BLE001 - log and continue, one bad symbol shouldn't kill the run
            row.update({"price": None, "prevClose": None, "changePct": None})
            row["status"] = "error"
            failures += 1
            print(f"WARN: failed to fetch {company['symbol']}: {exc}", file=sys.stderr)
        rows.append(row)

    output = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "companyCount": len(COMPANIES),
        "failedCount": failures,
        "companies": rows,
    }

    with open("data.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote data.json — {len(COMPANIES) - failures}/{len(COMPANIES)} quotes fetched successfully.")


if __name__ == "__main__":
    main()
