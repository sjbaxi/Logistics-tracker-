# NSE Logistics Manifest

A self-updating index of NSE-listed logistics/freight companies. A scheduled
job fetches quotes and commits them **whether or not anyone is viewing the
site** — that's the "even when nobody's looking" part.

## How it works

- `scripts/fetch_quotes.py` — fetches live quotes for the tracked companies
  and writes `data.json`.
- `.github/workflows/update-quotes.yml` — a GitHub Actions workflow that runs
  the script every 15 minutes during NSE trading hours (9:15 AM–3:30 PM IST,
  Mon–Fri) and commits `data.json` if it changed. This is the "server" — it
  runs on GitHub's infrastructure, not yours, and needs no machine of yours
  to stay on.
- `index.html` — a static page that reads `data.json` and renders the board.
  No backend needed to serve it.

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

4. **Kick off the first run manually** so you don't have to wait for the
   schedule: repo → Actions tab → "Update NSE logistics quotes" → "Run
   workflow". After it finishes (~30 seconds), refresh your Pages URL and
   real numbers should appear.

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

## Limits worth knowing

- GitHub Actions free tier gives public repos unlimited scheduled minutes;
  private repos get 2,000 free minutes/month, which this easily fits under
  at ~35 runs/day × ~30 sec each.
- The quote source is a public, unauthenticated market-data feed — reliable
  for personal/reference use but not licensed exchange data. For anything
  regulatory or financial-decision-critical, use NSE's official data
  products instead.
