"""Public S&P 500 constituent universe; not an exchange-wide stock listing."""
import io
import pandas as pd
import requests

SOURCE = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'

def load_sp500():
    response = requests.get(SOURCE, timeout=20, headers={'User-Agent':'Mozilla/5.0 (educational research application)'})
    response.raise_for_status()
    tables = pd.read_html(io.StringIO(response.text), match='Symbol')
    table = next(t for t in tables if 'Symbol' in t.columns and len(t) > 300)
    return list(dict.fromkeys(str(x).strip().replace('.', '-') for x in table['Symbol'].dropna()))
