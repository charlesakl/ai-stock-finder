# Phase 4: Broad-market screening

- Choose **S&P 500 (approximately 500 companies)** to load the current public index constituents (Wikipedia, may be temporarily unavailable).
- Select a scan cap (up to 550) and a horizon; click **Run market screen**. Data are retrieved from Yahoo Finance via yfinance in batches; large runs can take several minutes and may encounter rate limits.
- The scanner applies existing Phase 3 heuristic ranking to eligible stocks priced under $100, with sufficient price history. It selects the top declining candidate in each of three price bands; some bands can be empty.
- Optional **Automatically review the top three with six AI agents each** uses up to 18 billable OpenAI calls per scan. The research reports are shown under the selected candidates.
- Research is *not* a prediction of a market bottom or a verified buy recommendation. It uses public summary data and headline metadata, not independently verified financial filings or full-text news. No trades are placed.
- The universe is the S&P 500, **not all publicly traded U.S. companies**. Most S&P 500 constituents trade above $100 and are excluded from final candidates.
