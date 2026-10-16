# Phase 9 — Research evidence and top-three comparison

## What's new

- **Top stock research candidates**: a compact side-by-side comparison table, visible at the top of results in **Simple and Advanced** modes. Displays research rank, ticker, price, 30-day change, selected horizon, cautious recommendation, and SEC evidence status.
- **Specific descriptions**: Simple Mode's “Why it stands out” uses a shortened company-specific AI research explanation rather than identical boilerplate.
- **Optional SEC EDGAR evidence**: for up to three finalists only, the app retrieves recent 10-K/10-Q filing links and a small set of SEC XBRL facts, where available. Those facts are supplied to the six-agent review and Investment Committee. The app labels SEC evidence as available, never fully verified.
- **Honest evidence coverage**: no SEC credentials configured or an SEC request fails → no false claim of verification; the original Yahoo summary research continues.

## Enable SEC checks (optional)

Add this to your existing local `.env` (replace the placeholder with a real contact address):

```
SEC_USER_AGENT=AI Stock Finder Research contact@example.com
```

The SEC requires a descriptive User-Agent with contact information and fair-access behavior. The public EDGAR data APIs do not require an API key. See https://www.sec.gov/search-filings/edgar-application-programming-interfaces and https://www.sec.gov/about/developer-resources.

**Important:** SEC tagged XBRL facts may refer to different periods and definitions. Links and facts do not constitute full filing verification. News remains Yahoo Finance headline metadata, not independently verified article contents. An absent news feed does not imply no news exists. Bank capital, deposits, and credit data still need dedicated verification.

## How horizons work

The scanner's initial price/history eligibility filters are the same across horizons, so 500 stocks can produce the same initial 173 passing companies. Horizon changes the quantitative scoring weights and AI ranking, **not** the eligibility filter. That is expected behavior, not evidence that the horizon is ignored.

## Running

```powershell
py -3.13 -m venv .venv313
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv313\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Keep your existing `OPENAI_API_KEY` and `OPENAI_MODEL` in `.env`. Do not upload `.env` to GitHub.

## Validation

Python syntax and isolated SEC parsing tests were prepared. No live SEC, Yahoo Finance, Streamlit, or paid OpenAI integration tests were executed in the build environment. Full historical strategy validation is **not** included; do not interpret ranking as an established buy signal.
