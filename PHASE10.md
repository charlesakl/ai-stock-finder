# Phase 10 changes

- SEC XBRL values are accepted only if their reporting period is within 120 days of the most recent 10-Q/10-K reporting period. Old cash figures are omitted rather than shown as current. Duration concepts are restricted to quarter-length or annual-length periods and are labeled with their start/end dates. Missing data is explicitly displayed. This is still not a complete filing audit.
- Finalist selection uses documented horizon-aware weights: short-term prioritizes stabilization, medium-term balances quality and momentum, long-term emphasizes financial quality. Different horizons may still select the same stocks.
- Advanced stock details are now full-width, collapsed-by-default sections rather than three narrow columns. The top-three comparison table remains at the top.
- The existing five specialists plus synthesis (six OpenAI calls per stock) and Investment Committee are unchanged.

## Setup
Copy your own .env from your earlier project (do not commit it). SEC_USER_AGENT should contain a real contact email. Run `python -m pip install -r requirements.txt` then `python -m streamlit run app.py`.

## Limitations
No real-time trading advice, fully verified news, validated universe-level backtest, or guaranteed market bottoms. Horizon weights are design heuristics, not proven predictive factors.
