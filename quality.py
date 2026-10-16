"""Phase 6: transparent quality checks; third-party summary data, not audited filings."""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import math
import pandas as pd
import yfinance as yf

FIELDS = ('trailingPE','forwardPE','enterpriseToEbitda','freeCashflow','totalDebt','totalCash',
          'revenueGrowth','profitMargins','operatingMargins','marketCap','currentRatio','sector',
          'industry','priceToBook','returnOnEquity','returnOnAssets','bookValue')


def number(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError, OverflowError):
        return None


def technical_indicators(close):
    close = pd.to_numeric(close, errors='coerce').dropna()
    if len(close) < 200:
        return {'status':'Insufficient history'}
    last = float(close.iloc[-1])
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    if float(loss.iloc[-1]) == 0:
        rsi = 100.0 if float(gain.iloc[-1]) > 0 else 50.0
    else:
        rsi = 100 - 100/(1 + float(gain.iloc[-1]/loss.iloc[-1]))
    ema12 = close.ewm(span=12,adjust=False).mean()
    ema26 = close.ewm(span=26,adjust=False).mean()
    macd = ema12-ema26
    signal = macd.ewm(span=9,adjust=False).mean()
    sma50 = float(close.iloc[-50:].mean())
    sma200 = float(close.iloc[-200:].mean())
    support20 = float(close.iloc[-20:].min())
    return {'status':'Available','rsi14':round(rsi,1), 'sma50':round(sma50,2),
            'sma200':round(sma200,2),'macd_above_signal':bool(macd.iloc[-1]>signal.iloc[-1]),
            'above_sma50':bool(last>sma50),'above_sma200':bool(last>sma200),
            'low20':round(support20,2),'close':round(last,2)}


def assess(candidate, info, technical, retrieved_at):
    """Conservative deterministic checks. Missing inputs never receive positive points."""
    raw = {k: info.get(k) for k in FIELDS}
    metrics = {k: number(raw[k]) for k in FIELDS if k not in ('sector','industry')}
    metrics['sector'] = raw.get('sector') if isinstance(raw.get('sector'), str) else None
    metrics['industry'] = raw.get('industry') if isinstance(raw.get('industry'), str) else None
    checks = []
    flags = []
    score = 0
    observed = 0
    def add(name, result, weight, why):
        nonlocal score, observed
        checks.append({'check':name,'result':result,'weight':weight,'detail':why})
        if result is not None:
            observed += weight
            if result: score += weight
    fcf = metrics['freeCashflow']
    margin = metrics['profitMargins']
    growth = metrics['revenueGrowth']
    debt = metrics['totalDebt']
    cash = metrics['totalCash']
    pe = metrics['forwardPE'] or metrics['trailingPE']
    sector = (metrics.get('sector') or '').lower()
    industry = (metrics.get('industry') or '').lower()
    is_bank = 'bank' in industry
    if is_bank:
        pb, roe, roa = metrics['priceToBook'], metrics['returnOnEquity'], metrics['returnOnAssets']
        add('Positive profit margin', None if margin is None else margin > 0, 15, 'Bank summary margin; verify earnings')
        add('Nonnegative revenue growth', None if growth is None else growth >= 0, 15, 'Bank revenue is not a substitute for NIM or deposit trends')
        add('Positive P/E below 25', None if pe is None else 0 < pe < 25, 10, 'Verify normalized bank earnings')
        add('Price/book positive and <=2', None if pb is None else 0 < pb <= 2, 20, 'Book value is not tangible book; verify capital and asset quality')
        add('Positive return on equity', None if roe is None else roe > 0, 10, 'Verify ROE definition and time period')
        add('Positive return on assets', None if roa is None else roa > 0, 10, 'Verify ROA definition and time period')
        missing = [k for k in ('priceToBook','returnOnEquity','returnOnAssets','forwardPE') if metrics[k] is None]
        missing += ['CET1 / regulatory capital (not retrieved)', 'deposit trends (not retrieved)', 'credit quality (not retrieved)']
        # Critical banking evidence is absent: no bank gets an affirmative gate pass.
        flags.append('Bank-specific capital, deposit and credit metrics unverified')
    else:
        add('Positive free cash flow', None if fcf is None else fcf>0, 20, 'Summary FCF; verify in audited filings')
        add('Positive profit margin', None if margin is None else margin>0, 15, 'Summary profitability')
        add('Nonnegative revenue growth', None if growth is None else growth>=0, 15, 'Growth may be period-specific')
        add('Debt not greater than 3x cash', None if debt is None or cash is None else debt<=max(cash*3,0), 10, 'Crude leverage proxy; not appropriate for all industries')
        add('Positive P/E below 30', None if pe is None else 0<pe<30, 10, 'P/E alone does not establish fair value')
        missing = [k for k in ('freeCashflow','profitMargins','revenueGrowth','totalDebt','totalCash','forwardPE') if metrics[k] is None]
        if fcf is not None and fcf < 0: flags.append('Negative free cash flow')
        if margin is not None and margin < 0: flags.append('Unprofitable')
        if growth is not None and growth < -0.10: flags.append('Revenue contracting >10%')
        if debt is not None and cash is not None and debt > max(cash*5,1): flags.append('Debt >5x cash (sector dependent)')
    add('RSI between 30 and 60', None if technical.get('rsi14') is None else 30<=technical['rsi14']<=60, 10, 'Momentum context, not a bottom predictor')
    add('MACD above signal', technical.get('macd_above_signal'), 10, 'Momentum confirmation')
    add('Price above 50-day average', technical.get('above_sma50'), 10, 'Trend confirmation')
    if pe is not None and pe <= 0: flags.append('Nonpositive P/E')
    if technical.get('rsi14') is not None and technical['rsi14'] < 25: flags.append('Severely oversold; falling-knife risk')
    possible_weight = sum(c['weight'] for c in checks)
    # Different sector models have different possible totals (banks: 110, others: 100).
    # Normalize both dimensions, and never treat missing inputs as a pass.
    quality_pct = round(100 * score / possible_weight, 1) if possible_weight else 0.0
    coverage_pct = round(100 * observed / possible_weight, 1) if possible_weight else 0.0
    if observed < 60:
        stance = 'Insufficient evidence'
    elif is_bank:
        stance = 'Bank-specific verification needed'
    elif len(flags)>=2:
        stance = 'High value-trap risk'
    elif quality_pct>=65 and not flags:
        stance = 'Further research candidate'
    else:
        stance = 'Watch / verify'
    return {'ticker':candidate.ticker,'screen_score':candidate.score,'quality_points':quality_pct, 'earned_weight':score, 'possible_weight':possible_weight,
            'observed_weight':observed,'coverage_pct':coverage_pct,
            'status':stance,'flags':flags,'missing':missing,'metrics':metrics,
            'technical':technical,'checks':checks,'retrieved_at':retrieved_at,
            'source':'Yahoo Finance summary (yfinance); unverified; not audited SEC filings',
            'sector_model':'Banks: P/B, ROE, ROA; no debt/cash or FCF penalty' if is_bank else 'General corporate heuristic'}


def review(candidate):
    timestamp = datetime.now(timezone.utc).isoformat()
    ticker = yf.Ticker(candidate.ticker)
    info = ticker.info or {}
    history = ticker.history(period='2y', auto_adjust=True)
    if history is None or history.empty:
        raise ValueError('Price history unavailable')
    tech = technical_indicators(history['Close'])
    # Avoid comparing an old candidate quote with a fresh fundamental snapshot.
    if tech.get('close') and abs(tech['close'] / candidate.price - 1) > .05:
        raise ValueError('Latest price differs >5% from scan; rescan before evaluating')
    return assess(candidate, info, tech, timestamp)


def shortlist(found, per_band=5):
    from research import BANDS
    return [item for band in BANDS for item in sorted(
        (x for x in found if x.band==band and x.change_30d_pct<0 and x.drawdown_52w_pct<=-5),
        key=lambda x:x.score, reverse=True)[:per_band]]


def research_eligible(report):
    """Research eligibility is NOT approval to buy. Reject only clearly weak/unsupported leads."""
    if report['status'] in ('High value-trap risk', 'Insufficient evidence'):
        return False
    if report['coverage_pct'] < 60 or report['quality_points'] < 55:
        return False
    # Serious financial deterioration warrants verification before an AI finalist slot.
    critical = ('Negative free cash flow', 'Unprofitable', 'Revenue contracting >10%')
    if any(flag in report['flags'] for flag in critical):
        return False
    return True


def horizon_priority(candidate, report, horizon):
    """Research ordering heuristic only; never a buy signal."""
    technical = report.get('technical') or {}
    score = float(candidate.score)
    quality = float(report.get('quality_points') or 0)
    above50 = bool(technical.get('above_sma50'))
    above200 = bool(technical.get('above_sma200'))
    macd = bool(technical.get('macd_above_signal'))
    rsi = technical.get('rsi14')
    rsi = float(rsi) if isinstance(rsi, (float, int)) else 50.0
    if horizon.startswith('Short'):
        # More weight to recovery confirmation and recent momentum.
        return round(.35 * score + .20 * quality + (16 if above50 else 0) +
                     (8 if above200 else 0) + (8 if macd else 0) +
                     (8 if 40 <= rsi <= 65 else 0), 2)
    if horizon.startswith('Medium'):
        # Balance financial quality, price decline and technical confirmation.
        return round(.40 * quality + .40 * score + (10 if above50 else 0) +
                     (5 if macd else 0), 2)
    # Long-term research weights business quality most heavily.
    return round(.65 * quality + .25 * score + (10 if above200 else 0), 2)


def select_quality(found, reports, horizon='Medium (1–6 months)'):
    """Select eligible research leads by horizon, without requiring a buy verdict."""
    from research import BANDS
    by_ticker = {c.ticker: c for c in found}
    chosen = {}
    for band in BANDS:
        viable = [r for r in reports.values() if r['ticker'] in by_ticker
                  and by_ticker[r['ticker']].band == band and research_eligible(r)]
        best = max(viable, key=lambda r: (horizon_priority(by_ticker[r['ticker']], r, horizon),
                                         r['coverage_pct'], r['screen_score'])) if viable else None
        chosen[band] = by_ticker[best['ticker']] if best else None
    return chosen


def exploratory_backtest(close, hold_days=21):
    """Single-ticker walk-forward illustrative RSI+SMA strategy; NOT universe backtesting."""
    close = pd.to_numeric(close, errors='coerce').dropna()
    if len(close)<280: return {'status':'Insufficient history'}
    delta=close.diff()
    gains=delta.clip(lower=0).ewm(alpha=1/14,adjust=False).mean()
    losses=(-delta.clip(upper=0)).ewm(alpha=1/14,adjust=False).mean()
    rsi=100-100/(1+gains/losses.replace(0,float('nan')))
    sma=close.rolling(50).mean()
    # Signal at prior close, enter next close; cannot assume execution at prior close.
    signal=(rsi.shift(1).between(30,45) & (close.shift(1)>sma.shift(1))).fillna(False)
    events=[]; i=200
    while i+hold_days < len(close):
        if signal.iloc[i]:
            entry=float(close.iloc[i]); exit_price=float(close.iloc[i+hold_days]);
            events.append((exit_price/entry-1)*100-0.20) # 0.20% round-trip assumption
            i+=hold_days+1
        else: i+=1
    return {'status':'Available','trades':len(events),
            'mean_trade_return_pct':round(sum(events)/len(events),2) if events else None,
            'win_rate_pct':round(100*sum(x>0 for x in events)/len(events),1) if events else None,
            'hold_days':hold_days,'round_trip_cost_pct':0.20,
            'limitations':'Exploratory single-current-ticker test; subject to selection/survivorship bias. Not an S&P 500 strategy backtest; not risk-adjusted; no slippage model.'}


# Phase 11: transparent universe-wide selection, without a forced one-per-band rule.
def shortlist_universe(found, limit=24, per_band_floor=3):
    """Take leading candidates across the universe plus price-band representation.

    Price bands are for discovery, not hard caps on the three finalists.
    This is a limited fundamental-review shortlist, not full 500-stock verification.
    """
    from research import BANDS
    eligible = sorted((x for x in found if x.change_30d_pct < 0 and x.drawdown_52w_pct <= -5),
                      key=lambda x: (-x.score, x.ticker))
    chosen = {}
    for band in BANDS:
        for item in (x for x in eligible if x.band == band):
            if sum(x.band == band for x in chosen.values()) >= per_band_floor: break
            chosen[item.ticker] = item
    for item in eligible:
        if len(chosen) >= limit: break
        chosen.setdefault(item.ticker, item)
    return list(chosen.values())


def rank_quality_universe(found, reports, horizon):
    """Ordered evidence-backed research leads, including exclusions for transparency."""
    by_ticker = {c.ticker: c for c in found}
    rows = []
    for ticker, report in reports.items():
        item = by_ticker.get(ticker)
        if item is None: continue
        eligible = research_eligible(report)
        rows.append({'Stock': ticker, 'Price band': item.band, 'Screen score': item.score,
                     'Quality score': report.get('quality_points'),
                     'Horizon priority': horizon_priority(item, report, horizon),
                     'Eligible for research': eligible,
                     'Reason': 'Eligible for deeper research' if eligible else report.get('status', 'Evidence gap')})
    return sorted(rows, key=lambda r: (not r['Eligible for research'], -r['Horizon priority'], r['Stock']))


def select_quality_overall(found, reports, horizon, limit=3):
    by_ticker = {c.ticker: c for c in found}
    ranked = rank_quality_universe(found, reports, horizon)
    chosen = {}
    for row in ranked:
        if not row['Eligible for research']: continue
        item = by_ticker[row['Stock']]
        chosen[f'{item.band} · {item.ticker}'] = item
        if len(chosen) == limit: break
    return chosen


def select_screen_overall(found, limit=3):
    eligible = sorted((x for x in found if x.change_30d_pct < 0 and x.drawdown_52w_pct <= -5),
                      key=lambda x: (-x.score, x.ticker))
    return {f'{x.band} · {x.ticker}': x for x in eligible[:limit]}
