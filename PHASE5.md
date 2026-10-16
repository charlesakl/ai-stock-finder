# Phase 5 — Investment committee

Phase 5 compares the completed six-agent reviews for two or three selected finalists using one extra OpenAI request. It ranks **research priority**, not assured returns or an actionable buy order.

## Setup

Use Python 3.13; install `requirements.txt`, place your existing `.env` alongside `app.py`, then `python -m streamlit run app.py`. Do not commit `.env`.

## Workflow

1. Run market screen (up to ~500 S&P 500 constituents).
2. Enable automatic six-agent reviews. Optionally enable automatic investment committee comparison.
3. Alternatively run two or three manual reviews, then click **Compare reviewed stocks with investment committee**.
4. Inspect the ranked research priorities, risk factors and pre-entry verification requirements.

The committee uses existing specialist results only. No live validation of valuation, filings, support levels, or price bottoms. Missing/failed reports are not ranked. API charges apply.
