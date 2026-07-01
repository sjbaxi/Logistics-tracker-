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

## Limits worth knowing

- GitHub Actions free tier gives public repos unlimited scheduled minutes;
  private repos get 2,000 free minutes/month, which this easily fits under
  at ~35 runs/day × ~30 sec each.
- The quote source is a public, unauthenticated market-data feed — reliable
  for personal/reference use but not licensed exchange data. For anything
  regulatory or financial-decision-critical, use NSE's official data
  products instead.
