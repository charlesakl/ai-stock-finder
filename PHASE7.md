# Phase 7 — Sector-aware evidence and scan diagnostics

This version builds on Phase 6. It does **not** make stock-buy recommendations or claim to locate market bottoms.

## Improvements

1. The batch scanner separately counts (a) securities excluded by price/history rules and (b) securities whose prices could not be retrieved or processed. Missing tickers are retried once individually. A batch failure is not treated as an investment exclusion.
2. Regional-bank screening uses price/book, return on equity, return on assets, earnings and technical indicators. It does **not** apply ordinary corporate debt/cash and free-cash-flow checks to banks.
3. Banks are held at **Bank-specific verification needed**, even with strong summary ratios, because CET1, deposits, credit quality and other bank-specific measures are not fetched or verified.
4. The six-agent workflow receives the selected candidate's Phase 7 quality and technical report as additional input. It must treat missing evidence as missing.

## Limitations and next steps

- Yahoo Finance summary metrics are not SEC-audited source verification. SEC EDGAR integration, provenance and source timestamps remain future work.
- The nonbank scoring rubric remains a heuristic and is not an intrinsic-value estimate.
- Banks may now be excluded from final AI selection until verified regulatory and credit data are added. This is intentional.
- The scanner still selects at most one stock per price band; true sector diversification across all finalists and full-universe historical backtesting remain future work.
- Each of up to 3 finalists can trigger six OpenAI API calls plus one committee call. Disable automatic AI while testing the screen.
- Cached or previously stored results from a different code version should be refreshed with **Run market screen**.

## Run

Use Python 3.13 and install `requirements.txt` in the project directory. Copy your `.env` locally; do not commit it. Run `python -m streamlit run app.py`. Start with 100 stocks and disable automatic AI, then scale up once diagnostics look reasonable.
