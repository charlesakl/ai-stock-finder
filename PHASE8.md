# Phase 8 — Beginner-friendly interface (preview)

The app now defaults to **Simple** mode. Choose an investment horizon and click **Find opportunities**. The summary lists candidates in plain English, the risks, missing information, and the next research step. The six-agent and committee workflows can run automatically when selected; these use paid OpenAI API calls (up to 19 requests for three stocks). **Advanced** mode preserves the detailed Phase 7.1 reports, downloads, and diagnostics.

## Limitations
This is a user-interface improvement, not independently verified financial research. Yahoo Finance summary data can be stale or incomplete; the app does not validate SEC filings, verify news articles, estimate intrinsic value, or establish market bottoms. A ranking is **not** a buy recommendation. Historical tests are exploratory. No trading is performed.

## Next release gate
Add SEC filing reconciliation, verified news sources, persistent scan/report history, integration tests using mock market/API data, and beginner usability testing before treating this as a stable public v1.0.
