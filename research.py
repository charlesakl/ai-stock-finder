"""Deterministic, auditable research calculations; no trading orders."""
from dataclasses import dataclass
import math
import pandas as pd

BANDS = {'Under $20': (0, 20), '$20–$50': (20, 50), '$50–$100': (50, 100)}
HORIZONS = {'Short (1–30 days)': 21, 'Medium (1–6 months)': 126, 'Long (6–24 months)': 252}

@dataclass
class Candidate:
    ticker: str
    price: float
    change_30d_pct: float
    change_90d_pct: float
    drawdown_52w_pct: float
    volatility_annual_pct: float
    score: float
    band: str
    horizon: str
    asof: str
    rationale: str


def band_for_price(price):
    if not math.isfinite(price) or price <= 0: return None
    for band, (lo, hi) in BANDS.items():
        if lo < price < hi or (lo == 20 and price == 20) or (lo == 50 and price == 50):
            return band
    return None


def evaluate(ticker: str, close: pd.Series, horizon: str):
    close = pd.to_numeric(close, errors='coerce').dropna()
    if len(close) < 260: return None
    price = float(close.iloc[-1]); band = band_for_price(price)
    if band is None: return None
    d30 = (price / float(close.iloc[-22]) - 1) * 100
    d90 = (price / float(close.iloc[-64]) - 1) * 100
    peak = float(close.iloc[-252:].max())
    dd = (price / peak - 1) * 100
    daily = close.pct_change().dropna().iloc[-252:]
    vol = float(daily.std() * (252 ** .5) * 100)
    if not all(math.isfinite(v) for v in (d30,d90,dd,vol)): return None
    # Heuristic, not a forecast: rewards moderate dips, recent stabilization and lower volatility.
    dip = max(0, min(35, -dd))
    dip_points = 35 * max(0, 1 - abs(dip - 17) / 20)
    stabilization = max(0, min(30, 15 + d30))
    risk = max(0, 25 - vol / 4)
    trend = max(0, min(10, 5 + d90 / 6))
    if horizon.startswith('Short'):
        score = .30*dip_points + .35*stabilization + .25*risk + .10*trend
    elif horizon.startswith('Medium'):
        score = .35*dip_points + .25*stabilization + .30*risk + .10*trend
    else:
        score = .25*dip_points + .15*stabilization + .40*risk + .20*trend
    score = round(score / 35 * 100, 1)
    asof = str(close.index[-1].date()) if hasattr(close.index[-1], 'date') else str(close.index[-1])
    rationale = f'30-day change {d30:+.1f}%; 52-week drawdown {dd:.1f}%; annualized volatility {vol:.1f}%. Quantitative screen only; fundamentals and news not yet verified.'
    return Candidate(ticker, round(price,2),round(d30,1),round(d90,1),round(dd,1),round(vol,1),score,band,horizon,asof,rationale)


def select_candidates(items):
    """Best eligible declining stock per price band; never fill missing bands with fake picks."""
    out = {}
    for band in BANDS:
        eligible = [c for c in items if c and c.band == band and c.change_30d_pct < 0 and c.drawdown_52w_pct <= -5]
        out[band] = max(eligible, key=lambda c: c.score) if eligible else None
    return out
