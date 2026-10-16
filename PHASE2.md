# Phase 2 research extension

Use Python 3.13. Install `python -m pip install -r requirements.txt`. Copy `.env.example` to `.env` and add your OpenAI API key (never commit `.env`). Run `python -m streamlit run app.py`.

Select Phase 2 research in the sidebar, run a screen, and click **Research TICKER** under a selected candidate. Each click requests Yahoo Finance metadata/headlines and, if a key is configured, one OpenAI structured research response. API charges may apply.

The app does **not** read linked news articles, verify financial statements against SEC filings, guarantee fresh or complete data, or provide trade execution. News may be absent. Research output should be treated as a checklist, not personalized advice.

If you want a different supported model, set `OPENAI_MODEL` in `.env`.
