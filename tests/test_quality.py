from types import SimpleNamespace
import sys
import types
if "yfinance" not in sys.modules:
    try:
        import yfinance
    except ImportError:
        sys.modules["yfinance"] = types.ModuleType("yfinance")
import pandas as pd
from quality import assess, technical_indicators, exploratory_backtest, select_quality

def candidate(ticker='TEST', band='Under $20'):
    return SimpleNamespace(ticker=ticker,score=75,band=band)

def test_missing_data_does_not_pass():
    r=assess(candidate(),{}, {'status':'Insufficient history'}, '2026-10-15')
    assert r['status']=='Insufficient evidence'
    assert r['quality_points']==0

def test_positive_data_passes():
    info=dict(freeCashflow=100,profitMargins=.15,revenueGrowth=.12,totalDebt=100,totalCash=100,forwardPE=12)
    tech=dict(rsi14=45,macd_above_signal=True,above_sma50=True)
    r=assess(candidate(),info,tech,'2026-10-15')
    assert r['status']=='Further research candidate'
    assert r['quality_points']==100
    assert select_quality([candidate()],{'TEST':r})['Under $20'].ticker=='TEST'

def test_backtest_handles_no_signals():
    close=pd.Series([100+i*.1 for i in range(400)])
    result=exploratory_backtest(close)
    assert result['status']=='Available'
    assert result['trades']>=0
    assert 0<=technical_indicators(close)['rsi14']<=100

def test_bank_requires_bank_specific_verification():
    info=dict(sector='Financial Services',industry='Banks - Regional',priceToBook=1.1,
              returnOnEquity=.13,returnOnAssets=.01,profitMargins=.2,revenueGrowth=.04,
              forwardPE=9,totalDebt=10000,totalCash=10,freeCashflow=-500)
    tech=dict(rsi14=45,macd_above_signal=True,above_sma50=True)
    r=assess(candidate('BANK'),info,tech,'2026-10-15')
    assert r['status']=='Bank-specific verification needed'
    assert 'Debt >5x cash (sector dependent)' not in r['flags']
    assert 'Negative free cash flow' not in r['flags']
    assert 'deposit trends (not retrieved)' in r['missing']


def test_bank_scores_and_coverage_normalized_and_researchable():
    from quality import research_eligible
    info=dict(sector='Financial Services',industry='Banks - Regional',priceToBook=1.1,
              returnOnEquity=.13,returnOnAssets=.01,profitMargins=.2,revenueGrowth=.04,forwardPE=9)
    tech=dict(rsi14=45,macd_above_signal=True,above_sma50=True)
    c=candidate('BANK')
    r=assess(c,info,tech,'2026-10-15')
    assert r['quality_points']==100 and r['coverage_pct']==100
    assert r['status']=='Bank-specific verification needed'
    assert research_eligible(r)
    assert select_quality([c],{'BANK':r})['Under $20'].ticker=='BANK'

def test_bad_and_missing_data_do_not_become_finalists():
    from quality import research_eligible
    c=candidate()
    assert not research_eligible(assess(c,{}, {}, '2026-10-15'))
    info=dict(freeCashflow=-100,profitMargins=-.1,revenueGrowth=-.2,totalDebt=1000,totalCash=1,forwardPE=12)
    tech=dict(rsi14=45,macd_above_signal=True,above_sma50=True)
    r=assess(c,info,tech,'2026-10-15')
    assert not research_eligible(r)
    assert select_quality([c],{c.ticker:r})['Under $20'] is None
