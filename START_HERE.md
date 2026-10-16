# AI Stock Finder — Phase 11 Final

This is the Phase 11 cached edition with clearer green **BUY WATCH** markers near historical lower price bands and red **SELL WATCH** markers near upper bands. These markers are **not verified trade signals** and do not identify actual bottoms or tops. No trades are placed.

## Windows quick start
1. Extract the ZIP.
2. Open PowerShell inside the `ai-stock-research-agent` folder.
3. If you already have a working `.env` from Phase 11, copy it here. Never share it or commit it.
4. Run `py -3.13 start_stock_finder.py`. First launch creates `.venv313` and installs requirements; later launches skip installation.
5. Click **Find opportunities**, then scroll to the historical watch-zone chart and select a finalist.

If you change `requirements.txt`, delete `.venv313/.dependencies_installed` to reinstall.

## What the markers mean
Green BUY WATCH: price is at/below its 20-day moving average minus two standard deviations, with RSI below 35.
Red SELL WATCH: price is at/above its 20-day moving average plus two standard deviations, with RSI above 65.
Strong trends can continue despite markers; prices and markers are calculated from historical daily closes.
