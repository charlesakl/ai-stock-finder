import pandas as pd
from research import band_for_price, evaluate, select_candidates

def test_price_boundaries():
    assert band_for_price(19.99)=='Under $20'
    assert band_for_price(20)=='$20–$50'
    assert band_for_price(50)=='$50–$100'
    assert band_for_price(100) is None
    assert band_for_price(0) is None

def test_short_history_rejected():
    assert evaluate('TEST',pd.Series([10.0]*20),'Short (1–30 days)') is None

def test_candidate_and_selection():
    series=pd.Series([40.0]*240+[39.0]*10+[37.0]*10,index=pd.bdate_range('2024-01-01',periods=260))
    c=evaluate('TEST',series,'Medium (1–6 months)')
    assert c is not None and c.band=='$20–$50' and c.change_30d_pct < 0
    result=select_candidates([c])
    assert result['$20–$50'].ticker=='TEST'
    assert result['Under $20'] is None
