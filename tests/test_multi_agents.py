from multi_agents import SPECIALISTS, Decision

def test_specialists():
    assert set(SPECIALISTS) == {'Technical','News','Fundamentals','Industry','Risk'}

def test_decision_schema():
    d=Decision(status='Watch', thesis='test', reasons=[], risks=[], invalidation_triggers=[], additional_checks=[], bottom_claim='Not confirmed', confidence='low')
    assert d.status == 'Watch'
