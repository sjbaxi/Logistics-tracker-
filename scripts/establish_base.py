#!/usr/bin/env python3
"""
Establishes the base for a market-cap-weighted index, base date 1 April 2023,
base value 1000 — the same construction method NSE/S&P indices use:

    divisor          = (sum of base_price_i * shares_i) / base_index_value
    index_value(t)    = (sum of price_i(t) * shares_i) / divisor

Run this ONCE to set up the index, and again only when you deliberately want
to rebalance (e.g. change constituents, refresh share counts). It writes
base.json, which fetch_quotes.py then reads on every scheduled run — the
share counts and base prices stay LOCKED between rebalances, exactly like a
real index's periodic float-share review, so day-to-day index moves reflect
only price changes, not a shifting weighting scheme.

Companies that weren't listed yet on the base date (e.g. an IPO after
April 2023) can't have an April 2023 price. For those, this script falls
back to their first available trading day close as a proxy "entry price"
and flags them with baseIsProxy: true, so it's visible in the output which
constituents are exact vs. approximated.
"""
import json
import sys
import time
from datetime import datetime, timezone

import yfinance as yf

from companies import COMPANIES

BASE_DATE = datetime(2023, 4, 1).date()
BASE_INDEX_VALUE = 1000.0
MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 4


def get_base_price(ticker):
    """Returns (base_price, is_proxy, date_used_str)."""
    hist = ticker.history(start="2023-03-15", end="2023-04-10", auto_adjust=False)
    if not hist.empty:
        hist = hist.sort_index()
        on_or_before = hist[hist.index.date <= BASE_DATE]
        if not on_or_before.empty:
            row = on_or_before.iloc[-1]
            return float(row["Close"]), False, str(on_or_before.index[-1].date())
        row = hist.iloc[0]
        return float(row["Close"]), True, str(hist.index[0].date())

    # Not trading anywhere near the base date at all — likely IPO'd later.
    # Use the earliest available close as a proxy "entry price" instead.
    full_hist = ticker.history(period="max", auto_adjust=False)
    if full_hist.empty:
        raise ValueError("no historical price data available at all")
    full_hist = full_hist.sort_index()
    row = full_hist.iloc[0]
    return float(row["Close"]), True, str(full_hist.index[0].date())


def get_shares(ticker):
    shares = None
    try:
        shares = ticker.fast_info["shares"]
    except Exception:
        pass
    if not shares:
        try:
            shares = ticker.info.get("sharesOutstanding")
        except Exception:
            pass
    if not shares:
        raise ValueError("could not determine shares outstanding")
    return float(shares)


def establish_one(symbol):
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            base_price, is_proxy, date_used = get_base_price(ticker)
            shares = get_shares(ticker)
            return base_price, is_proxy, date_used, shares
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < MAX_ATTEMPTS:
                time.sleep(RETRY_DELAY_SECONDS)
    raise last_error


def main():
    companies_out = []
    for c in COMPANIES:
        symbol = c["symbol"]
        try:
            base_price, is_proxy, date_used, shares = establish_one(symbol)
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: could not establish base for {symbol}: {exc}", file=sys.stderr)
            continue
        companies_out.append({
            **c,
            "basePrice": round(base_price, 2),
            "baseDateUsed": date_used,
            "baseIsProxy": is_proxy,  # True = wasn't listed on 2023-04-01, using first-trade proxy
            "shares": shares,
        })
        time.sleep(1)

    if len(companies_out) < len(COMPANIES):
        missing = {c["symbol"] for c in COMPANIES} - {c["symbol"] for c in companies_out}
        print(f"WARNING: {len(missing)} companies could not be established: {sorted(missing)}", file=sys.stderr)

    if not companies_out:
        print("FATAL: no companies established, aborting without writing base.json", file=sys.stderr)
        sys.exit(1)

    base_total_mcap = sum(c["basePrice"] * c["shares"] for c in companies_out)
    divisor = base_total_mcap / BASE_INDEX_VALUE

    output = {
        "baseDate": BASE_DATE.isoformat(),
        "baseIndexValue": BASE_INDEX_VALUE,
        "baseTotalMarketCap": base_total_mcap,
        "divisor": divisor,
        "establishedAt": datetime.now(timezone.utc).isoformat(),
        "companies": companies_out,
    }

    with open("base.json", "w") as f:
        json.dump(output, f, indent=2)

    proxies = [c["symbol"] for c in companies_out if c["baseIsProxy"]]
    print(f"Established base for {len(companies_out)}/{len(COMPANIES)} companies.")
    if proxies:
        print(f"Used first-trade-day proxy (not an actual 1 Apr 2023 price) for: {proxies}")


if __name__ == "__main__":
    main()
