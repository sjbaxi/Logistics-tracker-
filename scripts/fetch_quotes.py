#!/usr/bin/env python3
"""
Fetches current quotes for the index constituents (defined once in
base.json — see establish_base.py) and writes data.json: per-company price,
change %, market cap in Rs crore, PLUS the market-cap-weighted index level
and its change from the previous close.

Index math (standard cap-weighted construction, matches base.json's divisor):
    index_value = (sum of price_i * shares_i) / divisor

Share counts come from base.json and are intentionally NOT refetched here —
real indices only revisit float/share counts on a periodic review, not on
every tick, so day-to-day moves reflect price only. Re-run establish_base.py
to rebalance shares or change constituents.

Runs on a schedule via .github/workflows/update-quotes.yml, whether or not
anyone is looking at the site.
"""
import json
import sys
import time
from datetime import datetime, timezone

import yfinance as yf

MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 4
CRORE = 10_000_000  # 1 crore = 1,00,00,000


def _extract(fast_info, keys):
    for key in keys:
        try:
            value = fast_info[key]
            if value is not None:
                return value
        except Exception:
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


def load_base():
    try:
        with open("base.json") as f:
            return json.load(f)
    except FileNotFoundError:
        print(
            "FATAL: base.json not found. Run scripts/establish_base.py once "
            "(Actions tab -> 'Establish index base' -> Run workflow) before "
            "the scheduled quote fetch can compute the index.",
            file=sys.stderr,
        )
        sys.exit(1)


def main():
    base = load_base()
    divisor = base["divisor"]

    rows = []
    failures = 0
    current_total_mcap = 0.0
    prev_total_mcap = 0.0

    for bc in base["companies"]:
        symbol = bc["symbol"]
        shares = bc["shares"]
        row = {"symbol": symbol, "name": bc["name"], "segment": bc["segment"]}
        try:
            q = fetch_quote(symbol)
            price, prev_close = q["price"], q["prevClose"]
            market_cap_cr = (price * shares) / CRORE
            row.update({
                "price": price,
                "prevClose": prev_close,
                "changePct": round((price - prev_close) / prev_close * 100, 2) if prev_close else None,
                "marketCapCr": round(market_cap_cr, 1),
                "status": "ok",
            })
            current_total_mcap += price * shares
            prev_total_mcap += (prev_close if prev_close else price) * shares
        except Exception as exc:  # noqa: BLE001
            failures += 1
            row.update({"price": None, "prevClose": None, "changePct": None, "marketCapCr": None, "status": "error"})
            print(f"WARN: failed to fetch {symbol} after retries: {exc}", file=sys.stderr)
            # Keep the index stable rather than skewed by a missing constituent:
            # hold its last-known (base) price flat for this run's total.
            current_total_mcap += bc["basePrice"] * shares
            prev_total_mcap += bc["basePrice"] * shares
        rows.append(row)
        time.sleep(1)

    ok_rows = [r for r in rows if r["marketCapCr"] is not None]
    failed_rows = [r for r in rows if r["marketCapCr"] is None]
    rows_sorted = sorted(ok_rows, key=lambda r: r["marketCapCr"], reverse=True) + failed_rows

    index_value = current_total_mcap / divisor
    prev_index_value = prev_total_mcap / divisor
    index_change_pct = (
        round((index_value - prev_index_value) / prev_index_value * 100, 2)
        if prev_index_value else None
    )

    output = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "index": {
            "baseDate": base["baseDate"],
            "baseValue": base["baseIndexValue"],
            "value": round(index_value, 2),
            "prevValue": round(prev_index_value, 2),
            "changePct": index_change_pct,
        },
        "companyCount": len(rows_sorted),
        "failedCount": failures,
        "companies": rows_sorted,
    }

    with open("data.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote data.json — index {index_value:.2f} ({index_change_pct}%), "
          f"{len(rows_sorted) - failures}/{len(rows_sorted)} quotes ok")


if __name__ == "__main__":
    main()
