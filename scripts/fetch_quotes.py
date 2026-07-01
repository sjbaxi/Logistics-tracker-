#!/usr/bin/env python3
"""
Fetches live quotes for a curated list of NSE-listed logistics companies
and writes them to data.json at the repo root.

Uses yfinance rather than raw HTTP calls to Yahoo's chart API: Yahoo now
frequently requires a session/crumb token, and yfinance handles that
negotiation (and retries) for us instead of returning bare 401/429s.

This script is run on a schedule by .github/workflows/update-quotes.yml —
it has no knowledge of whether anyone is looking at the site.
"""
import json
import sys
import time
from datetime import datetime, timezone

import yfinance as yf

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
    {"symbol": "ADANIPORTS","name": "Adani Ports & SEZ (APSEZ)",  "segment": "Ports / SEZ"},
    {"symbol": "JSWINFRA",  "name": "JSW Infrastructure",         "segment": "Ports / Terminals"},
]

MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 4


def _extract(fast_info, keys):
    """fast_info exposes both snake_case and camelCase keys depending on
    yfinance version; try a few until one works."""
    for key in keys:
        try:
            value = fast_info[key]
            if value is not None:
                return value
        except (KeyError, Exception):
            continue
    return None


def fetch_quote(symbol: str):
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            fast = ticker.fast_info
            price = _extract(fast, ["last_price", "lastPrice"])
            prev_close = _extract(fast, ["previous_close", "previousClose"])

            if price is None:
                # fast_info can come back empty for illiquid/small-cap symbols;
                # fall back to a 1-day price history.
                hist = ticker.history(period="2d")
                if not hist.empty:
                    price = float(hist["Close"].iloc[-1])
                    if prev_close is None and len(hist) > 1:
                        prev_close = float(hist["Close"].iloc[-2])

            if price is None:
                raise ValueError("no price available from fast_info or history")

            return {
                "price": round(float(price), 2),
                "prevClose": round(float(prev_close), 2) if prev_close else None,
            }
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < MAX_ATTEMPTS:
                time.sleep(RETRY_DELAY_SECONDS)
    raise last_error


def main():
    rows = []
    failures = 0
    for company in COMPANIES:
        row = dict(company)
        try:
            row.update(fetch_quote(company["symbol"]))
            row["changePct"] = (
                round((row["price"] - row["prevClose"]) / row["prevClose"] * 100, 2)
                if row.get("prevClose")
                else None
            )
            row["status"] = "ok"
        except Exception as exc:  # noqa: BLE001 - one bad symbol shouldn't kill the run
            row.update({"price": None, "prevClose": None, "changePct": None})
            row["status"] = "error"
            failures += 1
            print(f"WARN: failed to fetch {company['symbol']} after retries: {exc}", file=sys.stderr)
        rows.append(row)
        time.sleep(1)  # be polite to the upstream feed, avoid rate-limit blocks

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
