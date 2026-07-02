# NSE Logistics Manifest

A self-updating index of NSE-listed logistics/freight companies. A scheduled
job fetches quotes and commits them **whether or not anyone is viewing the
site** — that's the "even when nobody's looking" part.

## How it works

- `scripts/companies.py` — the master list of tracked constituents. Edit
  this one file to add/remove companies.
- `scripts/establish_base.py` — **run once** (or whenever you deliberately
  rebalance). Computes each constituent's price on the base date (1 April
  2023) and locks in current share counts, then writes `base.json` with a
  divisor — the same construction method real cap-weighted indices (NSE,
  S&P) use: `divisor = (Σ base_price × shares) / base_index_value`.
  Companies that IPO'd after the base date (e.g. JSW Infrastructure, TVS
  Supply Chain Solutions) don't have an April 2023 price — the script falls
  back to their first-ever trading day close as a proxy and flags it
  (`baseIsProxy: true`) in `base.json` so it's transparent which numbers are
  exact vs. approximated.
- `scripts/fetch_quotes.py` — runs on schedule, fetches current prices,
  computes each company's market cap in ₹ crore, and computes the index
  level: `index_value = (Σ price × locked_shares) / divisor`. Share counts
  come from `base.json` and are **not** refetched every run — real indices
  only revisit float/share counts on periodic review, not on every tick, so
  day-to-day index moves reflect price only.
- `.github/workflows/update-quotes.yml` — runs `fetch_quotes.py` every 15
  minutes during NSE trading hours (9:15 AM–3:30 PM IST, Mon–Fri) and
  commits `data.json` if it changed. This is the "server" — it runs on
  GitHub's infrastructure, not yours.
- `.github/workflows/establish-base.yml` — manual-only workflow that runs
  `establish_base.py` and commits `base.json`. You must run this once before
  the scheduled fetch will work (see step 4 below).
- `index.html` — a static page: an index-value headline banner up top with
  change from previous close, and a compact table below sorted by market
  cap descending. No backend needed to serve it.

## Deploy it (free, ~5 minutes)

1. **Create a new GitHub repository** (public or private) and push these
   files to it:
   ```bash
   cd nse-logistics-app
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo>.git
   git push -u origin main
   ```

2. **Enable GitHub Pages**: repo → Settings → Pages → Source: "Deploy from a
   branch" → Branch: `main`, folder `/ (root)` → Save. Your site will be live
   at `https://<your-username>.github.io/<your-repo>/`.

3. **Allow the workflow to push changes**: repo → Settings → Actions →
   General → "Workflow permissions" → select "Read and write permissions" →
   Save. (Without this, the scheduled job can fetch quotes but won't be able
   to commit them.)

4. **Establish the index base — required before anything else will work**:
   repo → Actions tab → "Establish index base" → "Run workflow". This
   computes `base.json` (base-date prices + locked share counts + divisor).
   It only needs to run once, and again only if you rebalance later.

5. **Kick off the first quote fetch manually** so you don't have to wait for
   the schedule: repo → Actions tab → "Update NSE logistics quotes" → "Run
   workflow". After it finishes (~30–60 seconds), refresh your Pages URL and
   the index value + company table should populate.

From then on, it updates itself every 15 minutes during market hours,
indefinitely, with no server to maintain and no cost.

## Customizing

- **Add/remove companies**: edit the `COMPANIES` list in
  `scripts/fetch_quotes.py` (symbols are NSE tickers; the script appends
  `.NS` automatically).
- **Change the schedule**: edit the `cron` line in
  `.github/workflows/update-quotes.yml`. Cron times are in UTC.
- **Manual refresh anytime**: Actions tab → "Run workflow", or just wait for
  the next scheduled tick.

## Troubleshooting: "prices aren't updating"

- **If you're looking at a single standalone HTML file with a "Refresh
  quotes" button** (an earlier version of this project): that approach
  can't work reliably. Yahoo Finance's API doesn't send CORS headers, so
  browsers block the page from fetching it directly — no refresh click or
  network setting fixes that, since it's Yahoo's server refusing the
  request, not a bug in the page. Use this repo's GitHub Actions version
  instead, which fetches server-side where CORS doesn't apply.
- **If `data.json` still shows `null` prices after deploying**: check the
  Actions tab → latest "Update NSE logistics quotes" run → expand "Fetch
  latest quotes" logs. Common causes:
  - Workflow hasn't run yet — trigger it manually (Actions → Run workflow).
  - "Workflow permissions" is set to read-only — see step 3 above.
  - Occasional upstream rate-limiting — the script retries 3× with a delay
    per symbol, but if Yahoo blocks the whole runner IP temporarily, wait
    for the next scheduled run.
- **If the page loads but shows the placeholder data forever**: make sure
  GitHub Pages is serving from the branch the workflow commits to (`main`),
  and that Pages has picked up the latest commit (check the Pages deployment
  log in the Actions tab).

## About the index methodology

- **Not free-float**: real indices like Nifty weight by *free-float* market
  cap (shares actually available to trade, excluding promoter/government
  lock-ins). This index uses total shares outstanding as a simpler proxy —
  transparent and reproducible, but it will weight promoter-heavy stocks
  more heavily than a free-float index would.
- **Historical share counts are approximated**: share counts as of April
  2023 aren't readily available via free data feeds, so `establish_base.py`
  uses *current* share counts for the base-period calculation too. If a
  constituent has done a buyback, split, or large issuance since 2023, the
  base contribution is slightly off. This is a common simplification, not
  unique to this project, but worth knowing.
- **New-constituent base prices are proxies**: JSW Infrastructure and TVS
  Supply Chain Solutions listed after April 2023, so their "base price" is
  actually their first trading day close, not an April 2023 price. Check
  `baseIsProxy` in `base.json` to see which companies this applies to.
- **Rebalancing**: this index does not auto-rebalance. If you add/remove
  companies in `companies.py`, re-run "Establish index base" — this resets
  the divisor, which will cause a one-time jump in the index level rather
  than a smooth chain-linked transition (real indices go through a more
  careful chain-linking process for this exact reason).

## Limits worth knowing

- GitHub Actions free tier gives public repos unlimited scheduled minutes;
  private repos get 2,000 free minutes/month, which this easily fits under
  at ~35 runs/day × ~30 sec each.
- The quote source is a public, unauthenticated market-data feed — reliable
  for personal/reference use but not licensed exchange data. For anything
  regulatory or financial-decision-critical, use NSE's official data
  products instead.
