# Phase 11 AI Modes

- **Free Research**: charts, screening and technical indicators; no OpenAI calls.
- **Budget AI** (default): manual per-stock short checklist, maximum 350 output tokens, 7-day cached responses.
- **Deep Research**: manual six-agent specialist reports and investment committee. Six agents may require six API calls per stock, plus a committee call.

The OpenAI API is billed separately from ChatGPT. Set usage budgets and alerts at https://platform.openai.com/settings/organization/limits. This application does not enforce a hard dollar spending cap. Cache hits depend on unchanged input evidence and model; changing stock prices can create new cache keys.

Launch: `py -3.13 start_stock_finder.py`. Copy your existing `.env` into the project folder; never publish it.
