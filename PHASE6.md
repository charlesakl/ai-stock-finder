# Phase 6: valuation and bottom-signal quality gate

This version builds on Phase 5. Tick **Phase 6: verify fundamentals and technical signals** to fetch financial-summary data and technical indicators for up to 15 quantitative shortlistees (up to 5 per price band). The quality gate uses an explicit points rubric, flags value-trap indicators and refuses to advance stocks with insufficient observed evidence. The top passing stock in each band then receives the existing six-agent AI reviews and investment-committee comparison when those checkboxes are enabled.

**Important limitations:** Metrics come from Yahoo Finance's summary feed, not verified SEC filings. No intrinsic/fair value is computed. P/E and leverage heuristics are not sector-normalized and can be misleading for banks, insurers, REITs, and cyclical businesses. An absent metric receives zero positive points and is flagged as missing. Some or all bands may have no passing candidate. This is an educational research aid, not investment advice.

**Exploratory backtest:** A button on each passing candidate runs a simple single-ticker historical RSI/50-day-average strategy with a 0.20% round-trip cost assumption, a one-day signal lag and non-overlapping holding periods. It is NOT a valid historical test of selecting the best stocks from the S&P 500, because it uses the current index constituents and current finalists (selection and survivorship bias). Results do not establish profitability or a bottom.

## Running

Use Python 3.13. Copy `.env` from your previous phase to this project directory. Do not commit `.env`. Install `python -m pip install -r requirements.txt`, then `python -m streamlit run app.py`.

Try 100 companies first, then 500. Additional company lookups may be rate-limited. For a reliable production-grade version, add a licensed financial data feed and reconcile metrics against SEC EDGAR filings, and implement point-in-time universe backtests.
