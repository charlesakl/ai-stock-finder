"""Phase 3: sequential specialist LLM assessments grounded in retrieved evidence.
No claim of exact bottom or automatic execution.
"""
import json
import os
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from openai import OpenAI
from agents import gather_evidence
from ai_cache import key_for, load, save

class SpecialistReport(BaseModel):
    findings: list[str]
    risks: list[str]
    missing_data: list[str]
    confidence: str = Field(description='low, medium or high')

class Decision(BaseModel):
    status: str = Field(description='Research candidate, Watch, Avoid, or Insufficient evidence')
    thesis: str
    reasons: list[str]
    risks: list[str]
    invalidation_triggers: list[str]
    additional_checks: list[str]
    bottom_claim: str
    confidence: str

SPECIALISTS = {
    'Technical': 'Assess price decline, volatility and momentum from numeric candidate metrics only. Use phase7_quality_report technical indicators when available; otherwise do not invent RSI, moving averages, support or market bottoms.',
    'News': 'Review headline titles, URLs and dates only. Do not claim full articles were read, and do not assume headlines explain a decline. Identify news gaps.',
    'Fundamentals': 'Assess provided summary company fundamentals and missing critical metrics. Never fabricate financial ratios, fair values, earnings or filings.',
    'Industry': 'Assess sector/industry context ONLY when supplied; otherwise flag absence of competitor and industry data.',
    'Risk': 'Challenge the bullish case. Identify value traps, liquidity, volatility, missing verification and downside scenarios using provided facts only.'
}

def _call(client, model, instructions, payload, schema):
    key = key_for('six-agent-v1:' + schema.__name__, model, instructions, payload)
    cached = load(key)
    if cached is not None:
        return cached
    response = client.responses.parse(model=model, instructions=instructions,
        input=json.dumps(payload, default=str), text_format=schema)
    if response.output_parsed is None:
        raise RuntimeError('Model returned no structured output')
    result = response.output_parsed.model_dump()
    save(key, result)
    return result

def run_research(candidate, model=None, evidence=None, quality_report=None, sec_report=None):
    evidence = evidence if evidence is not None else gather_evidence(candidate.ticker)
    if quality_report is not None:
        evidence = dict(evidence)
        evidence['phase7_quality_report'] = quality_report
    if sec_report is not None:
        evidence = dict(evidence)
        evidence['sec_edgar'] = sec_report
    client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    model = model or os.getenv('OPENAI_MODEL', 'gpt-4.1-mini')
    candidate_data = vars(candidate)
    reports = {}
    for role, task in SPECIALISTS.items():
        reports[role] = _call(client, model,
            'You are the '+role+' specialist in a stock research workflow. '+task+
            ' Use ONLY supplied data. Distinguish facts from hypotheses. If data is missing say so. '
            'Keep findings concise. confidence must be low, medium, or high. No trading instructions.',
            {'candidate':candidate_data,'evidence':evidence}, SpecialistReport)
    decision = _call(client, model,
        'You are a skeptical investment research synthesizer. Review all five specialist reports. '
        'Only use provided evidence; reports are fallible and may contain unsupported claims. '
        'Do not invent citations, valuation targets or certainty of a bottom. '
        'Allowed status EXACTLY: Research candidate, Watch, Avoid, Insufficient evidence. '
        'Prefer Insufficient evidence when critical fundamental or news evidence is missing. '
        'bottom_claim must explicitly say a market bottom cannot be confirmed. '
        'Do not provide personalized financial advice or place trades.',
        {'candidate':candidate_data,'evidence':evidence,'specialists':reports}, Decision)
    if decision['status'] not in {'Research candidate','Watch','Avoid','Insufficient evidence'}:
        decision['status']='Insufficient evidence'
    if decision['confidence'].lower() not in {'low','medium','high'}:
        decision['confidence']='low'
    decision['bottom_claim']='A stock-market bottom cannot be confirmed from these data.'
    return {'ticker':candidate.ticker,'asof':datetime.now(timezone.utc).isoformat(),
            'evidence':evidence,'specialists':reports,'decision':decision,
            'limitations':'Summary financial data and available technical indicators; no verified SEC filings, full articles, intrinsic fair-value model or reliable universe backtest.'}
