"""Compare completed six-agent reviews; no additional market data or trades."""
import json
import os
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from openai import OpenAI
from ai_cache import key_for, load, save

class RankedCandidate(BaseModel):
    ticker: str
    rank: int
    stance: str = Field(description='Research candidate, Watch, Avoid, or Insufficient evidence')
    rationale: str
    risks: list[str]
    entry_conditions: list[str]

class CommitteeResult(BaseModel):
    summary: str
    rankings: list[RankedCandidate]
    limitations: str

ALLOWED = {'Research candidate', 'Watch', 'Avoid', 'Insufficient evidence'}

def compare_candidates(reports: dict, horizon: str, model: str | None = None) -> dict:
    """Rank only supplied, completed reviews. Raises on inconsistent model output."""
    if len(reports) < 2:
        raise ValueError('At least two completed reports are required')
    payload = {}
    for ticker, report in reports.items():
        if ticker != report.get('ticker'):
            raise ValueError(f'Ticker mismatch for {ticker}')
        payload[ticker] = {
            'asof': report.get('asof'),
            'decision': report.get('decision'),
            'specialists': report.get('specialists'),
            'fundamentals': report.get('evidence', {}).get('fundamentals'),
            'news': report.get('evidence', {}).get('news'),
            'sec_edgar': report.get('evidence', {}).get('sec_edgar'),
            'limitations': report.get('limitations'),
        }
    resolved_model = model or os.getenv('OPENAI_MODEL', 'gpt-4.1-mini')
    instructions = (
        'You are a skeptical research committee comparing ONLY the supplied stocks for the specified investment horizon. '
        'Rank ALL candidates from strongest to weakest *research priority*, not probability of profit. '
        'A stock near its low is not necessarily undervalued. Do not invent valuation, entry prices, news, filings, '
        'technical indicators, returns, or confidence probabilities. No personalized buy instructions. '
        'Use stance exactly one of Research candidate, Watch, Avoid, Insufficient evidence. '
        'If evidence is inadequate, say Insufficient evidence even for rank 1. '
        'State concrete verifications required before considering an entry. '
        'Mention that no exact bottom can be determined and data may be stale.')
    data = {'horizon': horizon, 'candidates': payload}
    cache_key = key_for('committee-v1', resolved_model, instructions, data)
    result = load(cache_key)
    if result is None:
        client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
        response = client.responses.parse(model=resolved_model, instructions=instructions,
            input=json.dumps(data, default=str), text_format=CommitteeResult)
        if response.output_parsed is None:
            raise RuntimeError('No structured committee response returned')
        result = response.output_parsed.model_dump()
    ranked = result['rankings']
    if len(ranked) != len(reports) or set(x['ticker'] for x in ranked) != set(reports):
        raise ValueError('Committee response did not cover exactly the reviewed stocks')
    if sorted(x['rank'] for x in ranked) != list(range(1, len(reports)+1)):
        raise ValueError('Committee response ranks are invalid')
    for x in ranked:
        if x['stance'] not in ALLOWED:
            x['stance'] = 'Insufficient evidence'
    result['rankings'] = sorted(ranked, key=lambda x: x['rank'])
    result['limitations'] = ('No exact stock-market bottom can be confirmed. Rankings are research priorities, '
        'not verified buy signals. Based on potentially incomplete headline metadata, summary fundamentals '
        'and prior AI reports; SEC-tagged data (if available) is not full filing validation, intrinsic valuation or backtesting.')
    result['asof'] = datetime.now(timezone.utc).isoformat()
    result['horizon'] = horizon
    save(cache_key, result)
    return result
