# Phase 7.1 — Quality gate corrections

- Bank-specific checks total 110 raw weight, while corporate checks total 100. Both the quality score and evidence coverage now normalize against the actual sum of weights to stay between 0 and 100. Raw earned, observed and possible weights are retained in each report.
- Research eligibility is separate from the conservative status. Bank-specific verification needed and Watch/verify can proceed to specialist research when quality >=55, coverage >=60, and no severe deterioration flag is present. This is **not** approval to buy.
- If no candidates qualify for research, no forced selection occurs.
- The six-agent review button remains available for shortlisted finalists; automatic reviews and committee comparison continue to work.
- This release does **not** validate SEC filings, perform intrinsic valuation, or predict bottoms.

To run: `python -m pip install -r requirements.txt` then `python -m streamlit run app.py`. Copy your local `.env` privately into the project directory; never commit it.
