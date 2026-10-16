# AI Stock Finder — Phase 11 User Guide

## What this app does
AI Stock Finder screens stocks using historical prices and available third-party company summary data. It highlights research candidates and displays historical BUY WATCH / SELL WATCH markers. It is a research tool, not an investment adviser or trading system. No trades are placed.

## Quick start (Windows)
1. Extract the project ZIP and open PowerShell in `ai-stock-research-agent`.
2. Run `py -3.13 start_stock_finder.py`.
3. Choose a research mode, investment horizon, and stock universe.
4. Open **Screening Settings** to adjust the universe, screening limit, and optional financial/technical checks.
5. Click **Find opportunities**. Under **Top stock research candidates**, choose **Chart a finalist** to see its historical price-zone chart.

## Research modes
- **Free Research (default):** Stock screening, financial/technical checks, historical charts and BUY/SELL watch markers. No OpenAI API calls.
- **AI Research:** All Free Research features, plus optional one-analyst stock checklists. Click the stock's AI analysis button to initiate a paid request. Results can be cached for seven days.
- **Advanced AI Research:** All Free Research features, plus optional six-agent reviews and Investment Committee comparison. Run each analysis manually; API usage can be higher.

The research-mode selection does not change market-data provider charges or internet usage; "free" refers to OpenAI API calls in this application.

## Screening Settings
- **Stock universe:** Choose S&P 500 or Custom tickers. The comma-separated custom list is only used when **Custom tickers** is selected.
- **Maximum companies to scan:** Limits the number of S&P 500 companies processed.
- **Analyze financial health and technical indicators:** Adds checks of available financial-summary data and historical price signals for shortlisted stocks. It is not audited financial verification and does not establish fair value.

## Understanding BUY and SELL watch markers
Green **BUY WATCH** indicates a historical lower-price-band condition together with a low RSI. Red **SELL WATCH** indicates a historical upper-price-band condition together with a high RSI. The implementation uses a 20-day rolling average plus/minus two standard deviations, with RSI thresholds under 35 and over 65, respectively. Markers can be frequent, late, or misleading in strong trends. They do not mark guaranteed bottoms or tops and are not orders.

## OpenAI API cost controls
- Free Research is the safest mode for exploring without OpenAI token charges.
- AI Research and Advanced AI Research only make paid AI requests after you click the relevant analysis button.
- Identical AI requests may use cached responses for up to seven days. Changed inputs can cause a new paid request.
- ChatGPT subscriptions and OpenAI API billing are separate. Monitor usage and set account-level budgets in the OpenAI platform.
- Do not upload `.env`, API keys, local caches, or private data to GitHub.

## Data and analysis limitations
Market data can be stale, incomplete, delayed or rate-limited. Company financial summaries are not equivalent to audited filing analysis. Quantitative scores are screening heuristics, not expected returns or buy ratings. The app does not place trades.

## Troubleshooting
If the launcher fails, confirm Python 3.13 is installed and run `py -3.13 --version`. If dependencies change, remove `.venv313/.dependencies_installed` and relaunch. Keep your `.env` local if you use paid AI features.
