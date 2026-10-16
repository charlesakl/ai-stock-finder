"""Optional SEC EDGAR filing evidence, not a complete audited verification."""
import os
from datetime import datetime, timezone
import requests
from functools import lru_cache


def _get(url, agent):
    response = requests.get(url, headers={'User-Agent': agent, 'Accept-Encoding': 'gzip, deflate',
                                          'Accept': 'application/json'}, timeout=12)
    response.raise_for_status()
    return response.json()


def _latest_fact(facts, names, reference_end=None, max_age_days=120):
    """Use only tagged facts near the newest 10-Q/10-K period; do not backfill old cash.

    For duration concepts prefer the latest quarter (roughly 60–105 days),
    or an annual 10-K duration (roughly 330–380 days). This does not convert
    YTD into quarterly values. The period is always disclosed.
    """
    from datetime import date
    gaap = facts.get('facts', {}).get('us-gaap', {})
    if not reference_end:
        return None
    reference = date.fromisoformat(reference_end)
    choices = []
    for priority, name in enumerate(names):
        entries = gaap.get(name, {}).get('units', {}).get('USD', [])
        for x in entries:
            if x.get('form') not in ('10-K', '10-Q') or not x.get('filed') or x.get('val') is None or not x.get('end'):
                continue
            try:
                end = date.fromisoformat(x['end'])
                lag = (reference - end).days
                if not (0 <= lag <= max_age_days):
                    continue
                if x.get('start'):
                    duration = (end - date.fromisoformat(x['start'])).days + 1
                    if not (60 <= duration <= 105 or 330 <= duration <= 380):
                        continue
                choices.append((end, -priority, x['filed'], name, x))
            except (ValueError, TypeError):
                continue
    if not choices:
        return None
    end, _, _, name, latest = max(choices)
    return {'metric': name, 'value_usd': latest['val'], 'period_start': latest.get('start'),
            'period_end': latest.get('end'), 'filed': latest['filed'],
            'form': latest['form'], 'accession': latest.get('accn')}


@lru_cache(maxsize=2)
def _ticker_mapping(agent):
    return _get('https://www.sec.gov/files/company_tickers.json', agent)


def fetch_sec_evidence(ticker, agent=None):
    """Fetch public SEC filings and a few XBRL facts for a finalist only.

    SEC_USER_AGENT must identify the app and a real contact email. Failure is nonfatal.
    """
    agent = agent or os.getenv('SEC_USER_AGENT', '').strip()
    result = {'ticker': ticker, 'status': 'not_configured', 'retrieved_at': None,
              'facts': {}, 'filings': [], 'source': 'SEC EDGAR data.sec.gov'}
    if not agent or '@' not in agent:
        result['message'] = 'Set SEC_USER_AGENT with a real contact email to enable SEC checks.'
        return result
    try:
        mapping = _ticker_mapping(agent)
        match = next((x for x in mapping.values() if x.get('ticker', '').upper() == ticker.upper()), None)
        if not match:
            result.update(status='unavailable', message='Ticker not found in SEC mapping')
            return result
        cik = str(match['cik_str']).zfill(10)
        result['cik'] = cik
        submissions = _get(f'https://data.sec.gov/submissions/CIK{cik}.json', agent)
        recent = submissions.get('filings', {}).get('recent', {})
        for form, filed, accession, doc in zip(recent.get('form', []), recent.get('filingDate', []),
                                               recent.get('accessionNumber', []), recent.get('primaryDocument', [])):
            if form in ('10-K', '10-Q') and len(result['filings']) < 2:
                result['filings'].append({'form': form, 'filed': filed,
                    'url': f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{doc}"})
        # Latest filed 10-Q/10-K reporting period, not an arbitrary old XBRL tag.
        reference_end = next((end for form, end in zip(recent.get('form', []), recent.get('reportDate', []))
                              if form in ('10-Q', '10-K') and end), None)
        companyfacts = _get(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json', agent)
        concepts = {'revenue': ['RevenueFromContractWithCustomerExcludingAssessedTax', 'Revenues', 'SalesRevenueNet'],
                    'net_income': ['NetIncomeLoss'], 'cash': ['CashAndCashEquivalentsAtCarryingValue'],
                    'assets': ['Assets'], 'liabilities': ['Liabilities']}
        result['latest_reporting_period'] = reference_end
        result['facts'] = {label: fact for label, tags in concepts.items()
                           if (fact := _latest_fact(companyfacts, tags, reference_end)) is not None}
        result['missing_facts'] = [label for label in concepts if label not in result['facts']]
        result.update(status='available', retrieved_at=datetime.now(timezone.utc).isoformat(),
                      message='SEC-tagged facts; verify reporting periods and filing context before comparing.')
    except Exception as exc:
        result.update(status='unavailable', message=f'SEC request failed: {type(exc).__name__}')
    return result
