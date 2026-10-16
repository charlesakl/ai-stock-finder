# Phase 3 — Multi-agent research

This upgrade adds five specialist LLM calls (technical, news, fundamentals, industry, risk) followed by a skeptical synthesis call. Run the existing market screen, check **Phase 3**, and click **Run 6-agent review** on a selected candidate.

## Windows / VS Code

Open `ai-stock-research-agent` in VS Code. Create the environment with Python 3.13 (`py -3.13 -m venv .venv313`) and activate it. Install with `python -m pip install -r requirements.txt`. Copy your existing `.env` file into this project directory (beside `app.py`), keeping `.env` out of Git. Run `python -m streamlit run app.py`.

Set `OPENAI_API_KEY` and a model that your API account supports, e.g. `OPENAI_MODEL=gpt-4.1-mini`. Six calls per ticker incur API charges. This is a *research candidate* tool, not a buy signal, fair value estimate, or bottom detector. The starter ticker universe is limited; prices may be delayed; evidence includes summary fundamentals and news headlines only, not full articles or independently verified SEC filings. No trading orders are executed.
