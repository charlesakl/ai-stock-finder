# Phase 8 — Beginner-friendly interface

## Simple Mode (default)
- Select an investment horizon and click **Find opportunities**.
- The S&P 500 scan, financial quality checks, up to three six-agent reviews, and Investment Committee run automatically when an API key is configured.
- Candidate cards appear in committee research-priority order, with a short assessment, concern, and next step.
- Expand **View detailed research** to inspect the underlying AI explanation, screening score, risks, and data completeness.
- Summary data completeness is *not* verified financial evidence.
- No stock is represented as a confirmed bottom or automatic buy.

## Advanced Mode
- Keeps the configurable scanner, manual and automatic AI review, committee comparison, exports, and full research evidence.

## Cost and limitations
A full three-stock run may make up to 19 paid OpenAI API requests. Yahoo Finance summaries and AI output are not substitutes for SEC filings or professional due diligence.

## Testing
Python syntax compiled successfully. Full Streamlit and OpenAI integration was not tested in this environment.
