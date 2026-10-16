> **Phase 9 update:** See [PHASE9.md](PHASE9.md) for the top-three comparison table and optional SEC EDGAR evidence.

# AI Stock Research Agent — Phase 7

See [PHASE7.md](PHASE7.md) for changes, cautions and setup.

# AI Stock Research Agent — Phase 1

A Python + Streamlit market screener with optional OpenAI-generated *research checklists*. It evaluates three investment horizons and selects at most one declining stock in each price range: under $20, $20–$50, and $50–$100.

**Important:** This is a research prototype, not financial advice, a buy signal, or an automated trading system. No orders are placed. The model does **not** currently read live news, filings, or fundamentals; these are Phase 2 work. The optional LLM checklist is explicitly restricted to supplied numerical data and cannot validate an investment thesis.

## Setup (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

On macOS/Linux: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && streamlit run app.py`.

## Optional OpenAI setup

For local use, set `OPENAI_API_KEY` in your shell environment. For Streamlit Cloud, add it to **App settings → Secrets** as `OPENAI_API_KEY = "..."`. Never commit keys. The OpenAI API requires separate billing from a ChatGPT subscription. The app works without an API key; only the optional commentary requires one.

## Usage

1. Select Short (1–30 days), Medium (1–6 months), or Long (6–24 months).
2. Edit the ticker watchlist (max 75 tickers per run; this is **not** a whole-market scan).
3. Click **Run market screen**. Prices are downloaded from Yahoo Finance via `yfinance` and cached for 30 minutes.
4. Review up to three eligible declining stocks and the full CSV. A band may have no eligible stock.
5. Run the other two horizons to compare results.

## How ranking works

- Price bands are mutually exclusive: (0,20), [20,50), [50,100).
- At least 260 daily close observations are required.
- A stock must have a negative 30-trading-day return and be at least 5% below its 52-week high.
- A heuristic uses drawdown, 30-day stabilization, historical volatility, and 90-day momentum; weights vary by horizon.
- Scores are **relative screening heuristics**, not calibrated probabilities, valuation estimates, forecasts, or backtested returns.
- Market data may be delayed, revised, or unavailable. A current share price is not the same as an attractive valuation.

## Tests

```bash
pytest -q
```

## Codex next-step prompt

> Inspect this repository. Improve market data error handling, add verified fundamentals and dated news feeds with links, implement a transparent risk and valuation score, write tests with mocked API data, and never invent financial figures or execute trades. Preserve the three price bands and three horizons. Run the tests and summarize changes before committing.

## Phase 2 roadmap

- Dated, sourced news and SEC filings; sentiment only with provenance
- Revenue, cash flow, debt, valuation, liquidity, earnings calendar and sector comparisons
- Separate multi-agent research stages and evidence checks
- Backtests with survivorship bias and transaction costs accounted for
- Automated reports and historical recommendation tracking

## Deployment

Push the repository to GitHub without any `.env` or secrets, then deploy `app.py` on Streamlit Community Cloud. `yfinance` is a convenience data source; check its data terms and use a licensed market-data provider before commercial deployment.


See [PHASE5.md](PHASE5.md) for investment committee ranking.

## Phase 8: Simple and Advanced views

The default **Simple** view displays an approachable summary of candidates, missing evidence, and risks. Select **Advanced** in the sidebar to access the detailed six-agent reports, committee JSON, and quality diagnostics. See `PHASE8.md` for limitations.
