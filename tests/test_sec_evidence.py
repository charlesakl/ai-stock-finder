from unittest.mock import patch
from sec_evidence import _latest_fact, fetch_sec_evidence


def test_latest_fact_prefers_recent_filing():
    facts = {'facts': {'us-gaap': {'Assets': {'units': {'USD': [
        {'form': '10-K', 'filed': '2025-02-01', 'end': '2024-12-31', 'val': 100},
        {'form': '10-Q', 'filed': '2026-05-01', 'end': '2026-03-31', 'val': 120},
    ]}}}}}
    assert _latest_fact(facts, ['Assets'])['value_usd'] == 120


def test_missing_contact_does_not_request_sec():
    with patch('sec_evidence._get') as get:
        result = fetch_sec_evidence('UPS', agent='')
        assert result['status'] == 'not_configured'
        get.assert_not_called()


def test_sec_failure_is_nonfatal():
    with patch('sec_evidence._ticker_mapping', side_effect=TimeoutError):
        result = fetch_sec_evidence('UPS', agent='Stock Finder contact@example.com')
        assert result['status'] == 'unavailable'
