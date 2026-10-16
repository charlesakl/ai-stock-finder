"""Batch scanner with explicit exclusion and download failure diagnostics."""
import pandas as pd
import yfinance as yf
from research import evaluate

def screen_universe(tickers, horizon, on_progress=None, batch_size=35):
    found, diagnostics = [], {'excluded_by_filters': [], 'data_unavailable': []}
    for start in range(0, len(tickers), batch_size):
        batch = tickers[start:start+batch_size]
        try:
            frame = yf.download(batch, period='2y', interval='1d', auto_adjust=True,
                                progress=False, threads=True, group_by='ticker', timeout=30)
        except Exception:
            frame = pd.DataFrame()
        for ticker in batch:
            try:
                close = frame['Close'] if len(batch) == 1 else frame[ticker]['Close']
                if isinstance(close, pd.DataFrame): close = close.iloc[:, 0]
                if close is None or close.dropna().empty: raise ValueError('No prices')
            except (KeyError, TypeError, ValueError, IndexError):
                # Retry missing prices individually, once, before classifying as unavailable.
                try:
                    retry = yf.download(ticker, period='2y', interval='1d', auto_adjust=True,
                                        progress=False, threads=False, timeout=20)
                    close = retry['Close']
                    if isinstance(close, pd.DataFrame): close = close.iloc[:, 0]
                    if close.dropna().empty: raise ValueError('No prices')
                except Exception:
                    diagnostics['data_unavailable'].append(ticker)
                    continue
            try:
                candidate = evaluate(ticker, close, horizon)
                if candidate: found.append(candidate)
                else: diagnostics['excluded_by_filters'].append(ticker)
            except Exception:
                diagnostics['data_unavailable'].append(ticker)
        if on_progress: on_progress(min(1.0, (start+len(batch))/len(tickers)))
    return found, diagnostics
