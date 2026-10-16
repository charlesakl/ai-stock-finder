"""Evidence-grounded research agents. No orders or price predictions."""
import os
from datetime import datetime, timezone
import yfinance as yf

FIELDS = ('longName','sector','industry','marketCap','trailingPE','forwardPE','totalRevenue','revenueGrowth','profitMargins','totalDebt','totalCash','freeCashflow','website')

def gather_evidence(ticker):
    obj = yf.Ticker(ticker)
    warnings=[]
    try:
        info=obj.info or {}
    except Exception as exc:
        info={}; warnings.append(f'Fundamentals unavailable: {type(exc).__name__}')
    fundamentals={k:info.get(k) for k in FIELDS if info.get(k) is not None}
    try:
        raw=obj.news or []
    except Exception as exc:
        raw=[]; warnings.append(f'News unavailable: {type(exc).__name__}')
    news=[]
    for item in raw[:12]:
        c=item.get('content') or item
        headline=c.get('title') or item.get('title')
        link=(c.get('canonicalUrl') or {}).get('url') if isinstance(c.get('canonicalUrl'),dict) else c.get('link') or item.get('link')
        pub=c.get('pubDate') or item.get('providerPublishTime')
        if headline and link and str(link).startswith('http'):
            news.append({'title':str(headline),'url':str(link),'published':str(pub or 'Unknown')})
    if not news: warnings.append('No verifiable news headlines returned')
    return {'ticker':ticker,'retrieved_at':datetime.now(timezone.utc).isoformat(),'fundamentals':fundamentals,'news':news,'warnings':warnings,'data_source':'Yahoo Finance via yfinance; headlines and metadata only; articles not read'}

def analyze(candidate,evidence,model=None):
    from openai import OpenAI
    from pydantic import BaseModel
    class Assessment(BaseModel):
        news_assessment: str
        fundamentals_assessment: str
        industry_assessment: str
        bull_case: str
        bear_case: str
        research_verdict: str
        missing_information: list[str]
        sources_used: list[str]
    client=OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    import json
    payload={'candidate':vars(candidate),'evidence':evidence}
    resp=client.responses.parse(
        model=model or os.getenv('OPENAI_MODEL','gpt-4.1-mini'),
        instructions=('You are a cautious stock research assistant. Only use provided evidence. '
          'News contains headlines and metadata, NOT full articles; do not imply you read articles. '
          'Do not invent financials, citations, price targets, analyst ratings, or catalysts. '
          'Assess sector and industry only to extent grounded by provided evidence. '
          'If evidence is insufficient, explicitly say so and use research_verdict "Insufficient evidence". '
          'Never recommend executing trades or imply guaranteed returns. Cite URLs only from evidence.'),
        input=json.dumps(payload,default=str),text_format=Assessment)
    if resp.output_parsed is None: raise RuntimeError('No structured assessment returned')
    result=resp.output_parsed.model_dump()
    allowed={n['url'] for n in evidence['news']}
    result['sources_used']=[url for url in result['sources_used'] if url in allowed]
    return result
